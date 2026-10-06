/*
 * RIS Transceiver firmware — ONE image, runtime TX/RX roles (ble-runtime-0004).
 *
 * The same binary performs either side of the OBS/CLR protocol:
 * - TX: newline-delimited OBS/CLR on the protocol UART -> latched state,
 *   continuously broadcast with non-connectable BLE extended advertising.
 * - RX: BLE state transitions -> newline-delimited OBS/CLR on the protocol
 *   UART, with duplicate suppression (first OBS, then first CLR).
 *
 * Runtime mode (see protocol.h):
 * - Button 1 (board alias sw0) toggles the BLE PHY: LE Coded S=8 <-> LE 1M.
 * - Button 2 (board alias sw1) toggles the operating role: TX <-> RX.
 * - Button 3 (board alias sw2) toggles TX state in TX and cycles RX receive
 *   source: natural -> forced CLR -> forced OBS -> natural.
 * - Role and PHY are independent: switching one preserves the other.
 * - Boot default is TX + Coded S=8. No role persistence (no NVS/settings).
 *
 * Switching never reboots and never reflashes. TX->RX stops advertising,
 * drops partial UART input, resets the RX dedup epoch, and starts scanning
 * on the current PHY. RX->TX stops scanning, clears RX transient state,
 * re-initializes the TX latch to CLEAR, flushes stale UART bytes, and
 * starts advertising on the current PHY. The requested role becomes the
 * active role only after its transport starts successfully; on failure the
 * firmware falls back to the previous side when possible, and the role LEDs
 * never show a normal TX/RX pattern unless that role's transport is running.
 *
 * LEDs (board aliases): led1 stays on for TX role, led0 stays on for RX role.
 * In TX, led0 stays off for CLR and pulses while advertising OBS. In RX,
 * led1 pulses on receive events and led3 indicates forced receive mode.
 * led2 shows PHY: on = Coded S=8, off = 1M.
 *
 * Pure protocol/mode logic lives in protocol.h so host-side tests reuse it.
 */

#include <errno.h>
#include <stdbool.h>
#include <stdint.h>
#include <string.h>

#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/bluetooth/gap.h>
#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/drivers/uart.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/sys/util.h>

#include "protocol.h"

#define LED0_NODE DT_ALIAS(led0)
#define LED1_NODE DT_ALIAS(led1)
#define LED2_NODE DT_ALIAS(led2)
#define LED3_NODE DT_ALIAS(led3)
#define SW0_NODE  DT_ALIAS(sw0)
#define SW1_NODE  DT_ALIAS(sw1)
#define SW2_NODE  DT_ALIAS(sw2)

#if !DT_NODE_HAS_STATUS(LED0_NODE, okay)
#error "The selected board must provide the led0 devicetree alias"
#endif

#if !DT_NODE_HAS_STATUS(LED1_NODE, okay)
#error "The selected board must provide the led1 devicetree alias"
#endif

#if !DT_NODE_HAS_STATUS(LED2_NODE, okay)
#error "The selected board must provide the led2 devicetree alias for PHY indication"
#endif

#if !DT_NODE_HAS_STATUS(LED3_NODE, okay)
#error "The selected board must provide the led3 devicetree alias for RX stub indication"
#endif

#if !DT_NODE_HAS_STATUS(SW0_NODE, okay)
#error "The selected board must provide the sw0 devicetree alias for PHY switching"
#endif

#if !DT_NODE_HAS_STATUS(SW1_NODE, okay)
#error "The selected board must provide the sw1 devicetree alias for role switching"
#endif

#if !DT_NODE_HAS_STATUS(SW2_NODE, okay)
#error "The selected board must provide the sw2 devicetree alias for TX state switching"
#endif

#define STATE_CLEAR    TRANSCEIVER_STATE_CLEAR
#define STATE_OBSTACLE TRANSCEIVER_STATE_OBSTACLE
#define PROTOCOL_VERSION 0x01

/* Button debounce interval: edges closer than this are one press. */
#define BUTTON_DEBOUNCE_MS 200
#define ACTIVITY_PULSE_MS 80
#define RX_STUB_MODE_BLINK_MS 500
#define UART_RX_BUFFER_SIZE 32
#define UART_COMMAND_QUEUE_DEPTH 8
#define UART_OUTPUT_QUEUE_DEPTH 8
#define UART_RX_TIMEOUT_US 10000
#define UART_SWITCH_TIMEOUT_MS 100

struct uart_command {
	uint8_t state;
	int epoch;
};

K_MSGQ_DEFINE(uart_command_queue, sizeof(struct uart_command),
	      UART_COMMAND_QUEUE_DEPTH, 4);
K_MSGQ_DEFINE(uart_output_queue, sizeof(uint8_t),
	      UART_OUTPUT_QUEUE_DEPTH, 1);
K_SEM_DEFINE(uart_rx_disabled, 0, 1);
K_SEM_DEFINE(uart_tx_complete, 0, 1);

enum rx_stub_mode {
	RX_STUB_NATURAL = 0,
	RX_STUB_FORCE_CLEAR,
	RX_STUB_FORCE_OBSTACLE,
};

/*
 * Service Data AD value: 7bb4f91d-521f-4ee6-a9c8-43dca4bb6e11 in BLE
 * little-endian order, followed by protocol version and state.
 */
static uint8_t service_data[18] = {
	0x11, 0x6e, 0xbb, 0xa4, 0xdc, 0x43, 0xc8, 0xa9,
	0xe6, 0x4e, 0x1f, 0x52, 0x1d, 0xf9, 0xb4, 0x7b,
	PROTOCOL_VERSION, STATE_CLEAR,
};

static const struct gpio_dt_spec led0 = GPIO_DT_SPEC_GET(LED0_NODE, gpios);
static const struct gpio_dt_spec led1 = GPIO_DT_SPEC_GET(LED1_NODE, gpios);
static const struct gpio_dt_spec phy_led = GPIO_DT_SPEC_GET(LED2_NODE, gpios);
static const struct gpio_dt_spec rx_stub_led = GPIO_DT_SPEC_GET(LED3_NODE, gpios);
static const struct gpio_dt_spec phy_button = GPIO_DT_SPEC_GET(SW0_NODE, gpios);
static const struct gpio_dt_spec role_button = GPIO_DT_SPEC_GET(SW1_NODE, gpios);
static const struct gpio_dt_spec state_button = GPIO_DT_SPEC_GET(SW2_NODE, gpios);

/*
 * UART0 is the nRF52833 DK's J-Link VCOM route. Console backends are disabled
 * in prj.conf; this device is owned only by the OBS/CLR protocol transport.
 */
static const struct device *const protocol_uart = DEVICE_DT_GET(DT_NODELABEL(uart0));
static struct tx_line_parser uart_parser;
static uint8_t uart_rx_buffers[2][UART_RX_BUFFER_SIZE];
static uint8_t uart_rx_next_buffer = 1;
static uint8_t uart_tx_buffer[4];
static atomic_t uart_command_epoch = ATOMIC_INIT(0);
static atomic_t uart_commands_enabled = ATOMIC_INIT(0);
static atomic_t uart_tx_enabled = ATOMIC_INIT(0);
static atomic_t uart_tx_busy = ATOMIC_INIT(0);
static atomic_t uart_rx_active = ATOMIC_INIT(0);
static atomic_t uart_rx_restart_requested = ATOMIC_INIT(0);
K_MUTEX_DEFINE(uart_tx_lock);

static void uart_tx_work_handler(struct k_work *work);
K_WORK_DELAYABLE_DEFINE(uart_tx_work, uart_tx_work_handler);

/* Runtime mode. Boot default is TX + Coded S=8 (protocol.h). */
static struct tr_mode mode = {
	.role = TR_BOOT_ROLE,
	.phy = TR_BOOT_PHY,
};

/*
 * True while the ACTIVE role's BLE transport is running. LEDs show a role
 * pattern only when this is true, so they always reflect the actually
 * active role and never a merely requested one.
 */
static bool transport_active;

/* TX runtime state. */
static uint8_t tx_state = STATE_CLEAR;

/* RX runtime state. */
static int8_t received_state = TRANSCEIVER_RX_UNKNOWN;
static atomic_t rx_stub_mode = ATOMIC_INIT(RX_STUB_NATURAL);
static struct k_spinlock rx_state_lock;

static struct bt_le_ext_adv *advertiser;

static struct gpio_callback phy_button_cb;
static struct gpio_callback role_button_cb;
static struct gpio_callback state_button_cb;
static atomic_t phy_switch_request = ATOMIC_INIT(0);
static atomic_t role_switch_request = ATOMIC_INIT(0);
static atomic_t state_switch_request = ATOMIC_INIT(0);
static atomic_t rx_activity_request = ATOMIC_INIT(0);
static int64_t last_phy_button_ms;
static int64_t last_role_button_ms;
static int64_t last_state_button_ms;

static void tx_state_write(uint8_t state);

static int leds_init(void)
{
	const struct gpio_dt_spec *leds[] = { &led0, &led1, &phy_led, &rx_stub_led };
	size_t i;
	int err;

	for (i = 0; i < ARRAY_SIZE(leds); i++) {
		if (!gpio_is_ready_dt(leds[i])) {
			return -ENODEV;
		}
		err = gpio_pin_configure_dt(leds[i], GPIO_OUTPUT_INACTIVE);
		if (err) {
			return err;
		}
	}

	return 0;
}

/* One steady LED identifies the active role; the other reports radio activity. */
static void role_leds_update(void)
{
	(void)gpio_pin_set_dt(&led0, transport_active && mode.role == TR_ROLE_RX);
	(void)gpio_pin_set_dt(&led1, transport_active && mode.role == TR_ROLE_TX);
}

/* PHY indicator: led2 on = Coded S=8, off = 1M. Never touches role LEDs. */
static void phy_indicator_update(void)
{
	(void)gpio_pin_set_dt(&phy_led,
			      (mode.phy == TR_PHY_CODED_S8) ? 1 : 0);
}

static void rx_stub_indicator_update(int64_t now)
{
	enum rx_stub_mode stub_mode = (enum rx_stub_mode)atomic_get(&rx_stub_mode);
	bool on = (stub_mode == RX_STUB_FORCE_CLEAR) ||
		  (stub_mode == RX_STUB_FORCE_OBSTACLE &&
		   ((now / RX_STUB_MODE_BLINK_MS) % 2 == 0));

	(void)gpio_pin_set_dt(&rx_stub_led,
			      transport_active && mode.role == TR_ROLE_RX && on);
}

static void phy_button_isr(const struct device *dev, struct gpio_callback *cb,
			   uint32_t pins)
{
	int64_t now;

	ARG_UNUSED(dev);
	ARG_UNUSED(cb);
	ARG_UNUSED(pins);

	now = k_uptime_get();
	if (now - last_phy_button_ms < BUTTON_DEBOUNCE_MS) {
		return;
	}
	last_phy_button_ms = now;
	atomic_set(&phy_switch_request, 1);
}

static void role_button_isr(const struct device *dev, struct gpio_callback *cb,
			    uint32_t pins)
{
	int64_t now;

	ARG_UNUSED(dev);
	ARG_UNUSED(cb);
	ARG_UNUSED(pins);

	now = k_uptime_get();
	if (now - last_role_button_ms < BUTTON_DEBOUNCE_MS) {
		return;
	}
	last_role_button_ms = now;
	atomic_set(&role_switch_request, 1);
}

static void state_button_isr(const struct device *dev, struct gpio_callback *cb,
			     uint32_t pins)
{
	int64_t now;

	ARG_UNUSED(dev);
	ARG_UNUSED(cb);
	ARG_UNUSED(pins);

	now = k_uptime_get();
	if (now - last_state_button_ms < BUTTON_DEBOUNCE_MS) {
		return;
	}
	last_state_button_ms = now;
	atomic_set(&state_switch_request, 1);
}

static int button_init(const struct gpio_dt_spec *button,
		       struct gpio_callback *cb,
		       gpio_callback_handler_t handler)
{
	int err;

	if (!gpio_is_ready_dt(button)) {
		return -ENODEV;
	}

	err = gpio_pin_configure_dt(button, GPIO_INPUT);
	if (err) {
		return err;
	}

	err = gpio_pin_interrupt_configure_dt(button, GPIO_INT_EDGE_TO_ACTIVE);
	if (err) {
		return err;
	}

	gpio_init_callback(cb, handler, BIT(button->pin));

	return gpio_add_callback(button->port, cb);
}

static int buttons_init(void)
{
	int err;

	err = button_init(&phy_button, &phy_button_cb, phy_button_isr);
	if (err) {
		return err;
	}

	err = button_init(&role_button, &role_button_cb, role_button_isr);
	if (err) {
		return err;
	}

	return button_init(&state_button, &state_button_cb, state_button_isr);
}

/* Test-and-clear for the ISR-raised requests. */
static bool phy_switch_poll(void)
{
	return atomic_cas(&phy_switch_request, 1, 0);
}

static bool role_switch_poll(void)
{
	return atomic_cas(&role_switch_request, 1, 0);
}

static bool state_switch_poll(void)
{
	return atomic_cas(&state_switch_request, 1, 0);
}

static void rx_observation_reset(bool reset_stub_mode)
{
	k_spinlock_key_t key = k_spin_lock(&rx_state_lock);

	received_state = TRANSCEIVER_RX_UNKNOWN;
	atomic_set(&rx_activity_request, 0);
	if (reset_stub_mode) {
		atomic_set(&rx_stub_mode, RX_STUB_NATURAL);
	}
	k_spin_unlock(&rx_state_lock, key);
}

static void rx_stub_mode_advance(void)
{
	k_spinlock_key_t key = k_spin_lock(&rx_state_lock);
	enum rx_stub_mode next = (enum rx_stub_mode)
		((atomic_get(&rx_stub_mode) + 1) % 3);

	atomic_set(&rx_stub_mode, next);
	k_spin_unlock(&rx_state_lock, key);
}

/* Coded S=8 advertising: explicit S=8 coding requirement (established). */
static const struct bt_le_adv_param adv_params_coded = BT_LE_ADV_PARAM_INIT(
	BT_LE_ADV_OPT_EXT_ADV |
	BT_LE_ADV_OPT_CODED |
	BT_LE_ADV_OPT_REQUIRE_S8_CODING,
	BT_GAP_ADV_FAST_INT_MIN_2,
	BT_GAP_ADV_FAST_INT_MAX_2,
	NULL);

/* 1M advertising: same extended-advertising shape, default 1M PHY. */
static const struct bt_le_adv_param adv_params_1m = BT_LE_ADV_PARAM_INIT(
	BT_LE_ADV_OPT_EXT_ADV,
	BT_GAP_ADV_FAST_INT_MIN_2,
	BT_GAP_ADV_FAST_INT_MAX_2,
	NULL);

static int advertise_state(uint8_t state)
{
	const struct bt_data ad[] = {
		BT_DATA(BT_DATA_SVC_DATA128, service_data, sizeof(service_data)),
	};

	service_data[17] = state;
	return bt_le_ext_adv_set_data(advertiser, ad, ARRAY_SIZE(ad), NULL, 0);
}

/* Real and synthetic events share the same RX deduplication/output path. */
static void rx_process_state(uint8_t state, bool synthetic)
{
	enum rx_emit emit;
	uint8_t serial_state;
	k_spinlock_key_t key = k_spin_lock(&rx_state_lock);
	enum rx_stub_mode stub_mode = (enum rx_stub_mode)atomic_get(&rx_stub_mode);

	if ((!synthetic && stub_mode != RX_STUB_NATURAL) ||
	    (synthetic && stub_mode == RX_STUB_NATURAL)) {
		k_spin_unlock(&rx_state_lock, key);
		return;
	}

	atomic_set(&rx_activity_request, 1);
	int8_t previous_state = received_state;
	emit = rx_dedup_update(&received_state, state);
	if (emit == RX_EMIT_OBS || emit == RX_EMIT_CLR) {
		serial_state = (emit == RX_EMIT_OBS) ? STATE_OBSTACLE : STATE_CLEAR;
		if (k_msgq_put(&uart_output_queue, &serial_state, K_NO_WAIT) != 0) {
			/* Preserve the transition so the next matching packet retries it. */
			received_state = previous_state;
			emit = RX_EMIT_NONE;
		}
	}
	k_spin_unlock(&rx_state_lock, key);

	if (emit == RX_EMIT_OBS || emit == RX_EMIT_CLR) {
		k_work_schedule(&uart_tx_work, K_NO_WAIT);
	}
}

/* Serial OBS/CLR and Button 3 both write the same TX state latch. */
static void tx_state_write(uint8_t state)
{
	if (state == tx_state || (state != STATE_CLEAR && state != STATE_OBSTACLE)) {
		return;
	}

	if (advertise_state(state) == 0) {
		tx_state = state;
	}
}

static void tx_state_toggle(void)
{
	uint8_t requested = (tx_state == STATE_CLEAR) ? STATE_OBSTACLE : STATE_CLEAR;

	tx_state_write(requested);
}

static int tx_transport_start(uint8_t state)
{
	const struct bt_le_adv_param *params;
	int err;

	params = (mode.phy == TR_PHY_1M) ? &adv_params_1m : &adv_params_coded;

	err = bt_le_ext_adv_create(params, NULL, &advertiser);
	if (err) {
		advertiser = NULL;
		return err;
	}

	err = advertise_state(state);
	if (err) {
		return err;
	}

	return bt_le_ext_adv_start(advertiser, BT_LE_EXT_ADV_START_DEFAULT);
}

static void tx_transport_stop(void)
{
	if (advertiser != NULL) {
		(void)bt_le_ext_adv_stop(advertiser);
		(void)bt_le_ext_adv_delete(advertiser);
		advertiser = NULL;
	}
}

static void uart_tx_work_handler(struct k_work *work)
{
	uint8_t state;
	const char *line;
	int err;

	ARG_UNUSED(work);

	if (k_mutex_lock(&uart_tx_lock, K_NO_WAIT) != 0) {
		k_work_schedule(&uart_tx_work, K_MSEC(5));
		return;
	}

	if (!atomic_get(&uart_tx_enabled) ||
	    !atomic_cas(&uart_tx_busy, 0, 1)) {
		k_mutex_unlock(&uart_tx_lock);
		return;
	}

	if (k_msgq_get(&uart_output_queue, &state, K_NO_WAIT) != 0) {
		atomic_set(&uart_tx_busy, 0);
		k_mutex_unlock(&uart_tx_lock);
		return;
	}

	line = (state == STATE_OBSTACLE) ? "OBS\n" : "CLR\n";
	memcpy(uart_tx_buffer, line, sizeof(uart_tx_buffer));
	err = uart_tx(protocol_uart, uart_tx_buffer, sizeof(uart_tx_buffer),
		      SYS_FOREVER_US);
	if (err != 0) {
		atomic_set(&uart_tx_busy, 0);
		(void)k_msgq_put_front(&uart_output_queue, &state, K_NO_WAIT);
		k_work_schedule(&uart_tx_work, K_MSEC(50));
	}

	k_mutex_unlock(&uart_tx_lock);
}

static void uart_rx_bytes(const uint8_t *bytes, size_t length)
{
	size_t i;

	if (!atomic_get(&uart_commands_enabled)) {
		tx_line_parser_reset(&uart_parser);
		return;
	}

	for (i = 0; i < length; i++) {
		enum tx_cmd_action action =
			tx_line_parser_feed(&uart_parser, bytes[i]);
		struct uart_command command;

		if (action == TX_CMD_IGNORE) {
			continue;
		}

		command.state = (action == TX_CMD_SET_OBS) ?
			STATE_OBSTACLE : STATE_CLEAR;
		command.epoch = atomic_get(&uart_command_epoch);
		/* A full queue drops a complete command; it never changes state. */
		(void)k_msgq_put(&uart_command_queue, &command, K_NO_WAIT);
	}
}

static void protocol_uart_callback(const struct device *dev,
				   struct uart_event *event, void *user_data)
{
	int err;

	ARG_UNUSED(user_data);

	switch (event->type) {
	case UART_RX_RDY:
		uart_rx_bytes(&event->data.rx.buf[event->data.rx.offset],
			      event->data.rx.len);
		break;
	case UART_RX_BUF_REQUEST:
		err = uart_rx_buf_rsp(dev, uart_rx_buffers[uart_rx_next_buffer],
				      sizeof(uart_rx_buffers[0]));
		if (err == 0) {
			uart_rx_next_buffer ^= 1U;
		} else {
			atomic_set(&uart_rx_restart_requested, 1);
		}
		break;
	case UART_RX_DISABLED:
		atomic_set(&uart_rx_active, 0);
		k_sem_give(&uart_rx_disabled);
		break;
	case UART_RX_STOPPED:
		atomic_set(&uart_rx_restart_requested, 1);
		break;
	case UART_TX_DONE:
	case UART_TX_ABORTED:
		atomic_set(&uart_tx_busy, 0);
		k_sem_give(&uart_tx_complete);
		if (atomic_get(&uart_tx_enabled)) {
			k_work_schedule(&uart_tx_work, K_NO_WAIT);
		}
		break;
	case UART_RX_BUF_RELEASED:
	default:
		break;
	}
}

static int protocol_uart_start_rx(void)
{
	int err;

	uart_rx_next_buffer = 1;
	err = uart_rx_enable(protocol_uart, uart_rx_buffers[0],
			    sizeof(uart_rx_buffers[0]), UART_RX_TIMEOUT_US);
	if (err == 0) {
		atomic_set(&uart_rx_active, 1);
		atomic_set(&uart_rx_restart_requested, 0);
	}
	return err;
}

/*
 * Stop and restart asynchronous RX to discard DMA-buffered bytes at role
 * boundaries. The command epoch invalidates anything queued before the flush.
 */
static int protocol_uart_flush_rx(bool accept_commands)
{
	int err;

	atomic_set(&uart_commands_enabled, 0);
	k_sem_reset(&uart_rx_disabled);
	err = uart_rx_disable(protocol_uart);
	if (err == 0) {
		if (k_sem_take(&uart_rx_disabled,
			       K_MSEC(UART_SWITCH_TIMEOUT_MS)) != 0) {
			return -ETIMEDOUT;
		}
	} else if (err != -EFAULT) {
		return err;
	}

	tx_line_parser_reset(&uart_parser);
	k_msgq_purge(&uart_command_queue);
	(void)atomic_inc(&uart_command_epoch);

	err = protocol_uart_start_rx();
	if (err == 0) {
		atomic_set(&uart_commands_enabled, accept_commands ? 1 : 0);
	}
	return err;
}

static int protocol_uart_tx_quiesce(void)
{
	int err = 0;

	if (k_mutex_lock(&uart_tx_lock, K_MSEC(UART_SWITCH_TIMEOUT_MS)) != 0) {
		return -ETIMEDOUT;
	}

	atomic_set(&uart_tx_enabled, 0);
	k_work_cancel_delayable(&uart_tx_work);
	while (atomic_get(&uart_tx_busy)) {
		if (k_sem_take(&uart_tx_complete,
			       K_MSEC(UART_SWITCH_TIMEOUT_MS)) != 0) {
			err = uart_tx_abort(protocol_uart);
			if (err != 0 ||
			    k_sem_take(&uart_tx_complete,
				       K_MSEC(UART_SWITCH_TIMEOUT_MS)) != 0) {
				err = -ETIMEDOUT;
				break;
			}
			err = 0;
		}
	}
	if (err == 0) {
		k_msgq_purge(&uart_output_queue);
	}
	k_mutex_unlock(&uart_tx_lock);
	return err;
}

/* Restore the serial direction owned by the still-active BLE role. */
static void protocol_uart_resume_current_role(void)
{
	if (!atomic_get(&uart_rx_active)) {
		(void)protocol_uart_start_rx();
	}

	if (!transport_active) {
		return;
	}
	if (mode.role == TR_ROLE_TX) {
		atomic_set(&uart_commands_enabled, 1);
	} else {
		atomic_set(&uart_tx_enabled, 1);
		k_work_schedule(&uart_tx_work, K_NO_WAIT);
	}
}

static void uart_commands_process(void)
{
	struct uart_command command;

	while (k_msgq_get(&uart_command_queue, &command, K_NO_WAIT) == 0) {
		if (command.epoch != atomic_get(&uart_command_epoch) ||
		    !transport_active || mode.role != TR_ROLE_TX) {
			continue;
		}
		tx_state_write(command.state);
	}
}

static int protocol_uart_init(void)
{
	int err;

	if (!device_is_ready(protocol_uart)) {
		return -ENODEV;
	}
	tx_line_parser_reset(&uart_parser);
	err = uart_callback_set(protocol_uart, protocol_uart_callback, NULL);
	if (err != 0) {
		return err;
	}
	return protocol_uart_start_rx();
}

static bool parse_ad(struct bt_data *data, void *user_data)
{
	uint8_t state;

	ARG_UNUSED(user_data);

	if (data->type != BT_DATA_SVC_DATA128 || data->data_len != sizeof(service_data)) {
		return true;
	}

	if (memcmp(data->data, service_data, 16) != 0 ||
	    data->data[16] != PROTOCOL_VERSION) {
		return true;
	}

	state = data->data[17];
	if (state != STATE_CLEAR && state != STATE_OBSTACLE) {
		return false;
	}

	/* Forced modes discard real packets; Natural uses the shared RX path. */
	rx_process_state(state, false);

	return false;
}

static void scan_received(const struct bt_le_scan_recv_info *info,
			  struct net_buf_simple *buffer)
{
	ARG_UNUSED(info);
	bt_data_parse(buffer, parse_ad, NULL);
}

static struct bt_le_scan_cb scan_callbacks = {
	.recv = scan_received,
};

/* 1M mode scans 1M only; coded mode scans coded only (established). */
static uint8_t rx_scan_options(void)
{
	if (mode.phy == TR_PHY_1M) {
		return 0;
	}
	return BT_LE_SCAN_OPT_CODED | BT_LE_SCAN_OPT_NO_1M;
}

static int rx_transport_start(void)
{
	const struct bt_le_scan_param params = {
		.type = BT_LE_SCAN_TYPE_PASSIVE,
		.options = rx_scan_options(),
		.interval = BT_GAP_SCAN_FAST_INTERVAL,
		.window = BT_GAP_SCAN_FAST_WINDOW,
	};

	return bt_le_scan_start(&params, NULL);
}

static void rx_transport_stop(void)
{
	(void)bt_le_scan_stop();
}

/*
 * Enter RX: stop advertising, drop partial UART input, start a fresh RX
 * observation epoch on the current PHY. The role commits to RX only if
 * scanning starts; otherwise the previous TX side is restored when
 * possible. PHY is preserved.
 */
static int switch_to_rx(void)
{
	int err;

	err = protocol_uart_tx_quiesce();
	if (err != 0) {
		protocol_uart_resume_current_role();
		return err;
	}
	err = protocol_uart_flush_rx(false);
	if (err != 0) {
		protocol_uart_resume_current_role();
		return err;
	}

	tx_transport_stop();
	rx_observation_reset(true);

	err = rx_transport_start();
	if (err) {
		if (tx_transport_start(tx_state) == 0) {
			transport_active = true;
			protocol_uart_resume_current_role();
			return err;
		}
		/* Neither side runs: role LEDs go dark instead of showing
		 * a normal TX pattern. A later button press retries. */
		transport_active = false;
		(void)gpio_pin_set_dt(&led0, 0);
		(void)gpio_pin_set_dt(&led1, 0);
		return err;
	}

	mode.role = TR_ROLE_RX;
	transport_active = true;
	atomic_set(&uart_tx_enabled, 1);
	k_work_schedule(&uart_tx_work, K_NO_WAIT);
	(void)gpio_pin_set_dt(&led1, 0);
	return 0;
}

/*
 * Enter TX: stop scanning, clear RX transient state, re-initialize the TX
 * latch to CLEAR, flush stale UART bytes, advertise on the current PHY.
 * The role commits to TX only if advertising starts; otherwise the
 * previous RX side is restored when possible. PHY is preserved.
 */
static int switch_to_tx(void)
{
	int err;

	err = protocol_uart_tx_quiesce();
	if (err != 0) {
		protocol_uart_resume_current_role();
		return err;
	}
	err = protocol_uart_flush_rx(false);
	if (err != 0) {
		protocol_uart_resume_current_role();
		return err;
	}

	rx_transport_stop();
	rx_observation_reset(true);
	tx_state = STATE_CLEAR;

	err = tx_transport_start(tx_state);
	if (err) {
		if (rx_transport_start() == 0) {
			transport_active = true;
			protocol_uart_resume_current_role();
			return err;
		}
		/* Neither side runs: role LEDs go dark instead of showing
		 * a normal RX pattern. A later button press retries. */
		transport_active = false;
		(void)gpio_pin_set_dt(&led0, 0);
		(void)gpio_pin_set_dt(&led1, 0);
		return err;
	}

	mode.role = TR_ROLE_TX;
	transport_active = true;
	atomic_set(&uart_commands_enabled, 1);
	return 0;
}

/* PHY switch on the current role. Role is preserved. */
static void switch_phy(void)
{
	enum tr_phy prev = mode.phy;

	tr_press_phy_button(&mode);
	if (mode.role == TR_ROLE_TX) {
		tx_transport_stop();
		if (tx_transport_start(tx_state) != 0) {
			/* Best effort: fall back to the previous PHY. */
			mode.phy = prev;
			(void)tx_transport_start(tx_state);
		}
	} else {
		rx_transport_stop();
		/* New PHY = new observation epoch; avoids stale state. */
		rx_observation_reset(false);
		(void)rx_transport_start();
	}
	phy_indicator_update();
}

static void role_switch_requested(void)
{
	if (mode.role == TR_ROLE_TX) {
		(void)switch_to_rx();
	} else {
		(void)switch_to_tx();
	}
}

static void transceiver_run(void)
{
	int64_t next_tx_pulse = k_uptime_get() + CONFIG_TRANSCEIVER_BLINK_INTERVAL_MS;
	int64_t next_rx_stub_event = 0;
	int64_t activity_until = 0;

	for (;;) {
		int64_t now;

		if (role_switch_poll()) {
			role_switch_requested();
			next_tx_pulse = k_uptime_get() +
					CONFIG_TRANSCEIVER_BLINK_INTERVAL_MS;
			if (mode.role == TR_ROLE_RX) {
				next_rx_stub_event = k_uptime_get() +
						     CONFIG_TRANSCEIVER_RX_STUB_INTERVAL_MS;
			}
			activity_until = 0;
		}

		if (phy_switch_poll()) {
			switch_phy();
		}

		/* UART callbacks frame commands; only complete lines reach this loop. */
		uart_commands_process();
		if (atomic_cas(&uart_rx_restart_requested, 1, 0)) {
			(void)protocol_uart_flush_rx(mode.role == TR_ROLE_TX &&
						     transport_active);
		}
		if (state_switch_poll() && transport_active) {
			if (mode.role == TR_ROLE_TX) {
				tx_state_toggle();
			} else {
				rx_stub_mode_advance();
				next_rx_stub_event = k_uptime_get();
				activity_until = 0;
			}
		}

		now = k_uptime_get();
		if (mode.role == TR_ROLE_RX && transport_active &&
		    now >= next_rx_stub_event) {
			enum rx_stub_mode stub_mode =
				(enum rx_stub_mode)atomic_get(&rx_stub_mode);

			if (stub_mode == RX_STUB_FORCE_CLEAR ||
			    stub_mode == RX_STUB_FORCE_OBSTACLE) {
				rx_process_state(stub_mode == RX_STUB_FORCE_CLEAR ?
						 STATE_CLEAR : STATE_OBSTACLE, true);
				next_rx_stub_event = now +
					CONFIG_TRANSCEIVER_RX_STUB_INTERVAL_MS;
			}
		}
		if (mode.role == TR_ROLE_TX && transport_active &&
		    tx_state == STATE_OBSTACLE && now >= next_tx_pulse) {
			activity_until = now + ACTIVITY_PULSE_MS;
			next_tx_pulse = now + CONFIG_TRANSCEIVER_BLINK_INTERVAL_MS;
		} else if (mode.role == TR_ROLE_TX && tx_state == STATE_CLEAR) {
			activity_until = 0;
		}
		if (atomic_cas(&rx_activity_request, 1, 0) &&
		    mode.role == TR_ROLE_RX && transport_active) {
			activity_until = now + ACTIVITY_PULSE_MS;
		}
		role_leds_update();
		rx_stub_indicator_update(now);
		(void)gpio_pin_set_dt(mode.role == TR_ROLE_TX ? &led0 : &led1,
				      transport_active && now < activity_until &&
			      (mode.role == TR_ROLE_RX || tx_state == STATE_OBSTACLE));

		k_sleep(K_MSEC(5));
	}
}

int main(void)
{
	int err;

	err = leds_init();
	if (err) {
		return err;
	}

	err = buttons_init();
	if (err) {
		return err;
	}
	err = protocol_uart_init();
	if (err) {
		return err;
	}
	phy_indicator_update();

	err = bt_enable(NULL);
	if (err) {
		return err;
	}

	bt_le_scan_cb_register(&scan_callbacks);

	/* Boot default: TX + Coded S=8. */
	err = tx_transport_start(tx_state);
	if (err) {
		return err;
	}
	transport_active = true;
	atomic_set(&uart_commands_enabled, 1);
	role_leds_update();
	transceiver_run();

	return 0;
}
