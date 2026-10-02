/*
 * RIS Transceiver firmware — ONE image, runtime TX/RX roles (ble-runtime-0004).
 *
 * The same binary performs either side of the OBS/CLR protocol:
 * - TX: newline-delimited OBS/CLR on the board console -> latched state,
 *   continuously broadcast with non-connectable BLE extended advertising.
 * - RX: BLE state transitions -> newline-delimited OBS/CLR on the board
 *   console, with duplicate suppression (first OBS, then first CLR).
 *
 * Runtime mode (see protocol.h):
 * - Button 1 (board alias sw0) toggles the BLE PHY: LE Coded S=8 <-> LE 1M.
 * - Button 2 (board alias sw1) toggles the operating role: TX <-> RX.
 * - Button 3 (board alias sw2) toggles the TX state: CLR <-> OBS in TX role.
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
 * led1 pulses on valid packets. led2 shows PHY: on = Coded S=8, off = 1M.
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
#include <zephyr/sys/printk.h>
#include <zephyr/sys/util.h>

#include "protocol.h"

#define LED0_NODE DT_ALIAS(led0)
#define LED1_NODE DT_ALIAS(led1)
#define LED2_NODE DT_ALIAS(led2)
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
static const struct gpio_dt_spec phy_button = GPIO_DT_SPEC_GET(SW0_NODE, gpios);
static const struct gpio_dt_spec role_button = GPIO_DT_SPEC_GET(SW1_NODE, gpios);
static const struct gpio_dt_spec state_button = GPIO_DT_SPEC_GET(SW2_NODE, gpios);

static const struct device *const console = DEVICE_DT_GET(DT_CHOSEN(zephyr_console));

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
static char uart_line[8];
static size_t uart_len;

/* RX runtime state. */
static int8_t received_state = TRANSCEIVER_RX_UNKNOWN;

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

static int leds_init(void)
{
	const struct gpio_dt_spec *leds[] = { &led0, &led1, &phy_led };
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

/* Drain stale bytes so pre-switch input can never become a TX command. */
static void uart_flush(void)
{
	uint8_t byte;

	while (uart_poll_in(console, &byte) == 0) {
		;
	}
	uart_len = 0;
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

	/* Mark every valid Transceiver packet, including repeated state packets. */
	atomic_set(&rx_activity_request, 1);

	switch (rx_dedup_update(&received_state, state)) {
	case RX_EMIT_OBS:
		printk("OBS\n");
		break;
	case RX_EMIT_CLR:
		printk("CLR\n");
		break;
	default:
		break;
	}

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

	tx_transport_stop();
	uart_len = 0;
	received_state = TRANSCEIVER_RX_UNKNOWN;

	err = rx_transport_start();
	if (err) {
		printk("ERR scan-start %d\n", err);
		if (tx_transport_start(tx_state) == 0) {
			transport_active = true;
			return err;
		}
		printk("ERR adv-restore\n");
		/* Neither side runs: role LEDs go dark instead of showing
		 * a normal TX pattern. A later button press retries. */
		transport_active = false;
		(void)gpio_pin_set_dt(&led0, 0);
		(void)gpio_pin_set_dt(&led1, 0);
		return err;
	}

	mode.role = TR_ROLE_RX;
	transport_active = true;
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

	rx_transport_stop();
	received_state = TRANSCEIVER_RX_UNKNOWN;
	tx_state = STATE_CLEAR;
	uart_flush();

	err = tx_transport_start(tx_state);
	if (err) {
		printk("ERR adv-start %d\n", err);
		received_state = TRANSCEIVER_RX_UNKNOWN;
		if (rx_transport_start() == 0) {
			transport_active = true;
			return err;
		}
		printk("ERR scan-restore\n");
		/* Neither side runs: role LEDs go dark instead of showing
		 * a normal RX pattern. A later button press retries. */
		transport_active = false;
		(void)gpio_pin_set_dt(&led0, 0);
		(void)gpio_pin_set_dt(&led1, 0);
		return err;
	}

	mode.role = TR_ROLE_TX;
	transport_active = true;
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
			if (tx_transport_start(tx_state) != 0) {
				printk("ERR adv-restart\n");
			}
		}
	} else {
		rx_transport_stop();
		/* New PHY = new observation epoch; avoids stale state. */
		received_state = TRANSCEIVER_RX_UNKNOWN;
		if (rx_transport_start() != 0) {
			printk("ERR scan-restart\n");
		}
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

static void tx_poll_uart(void)
{
	uint8_t byte;
	int err = uart_poll_in(console, &byte);

	if (err != 0) {
		return;
	}

	if (byte == '\r' || byte == '\n') {
		if (uart_len > 0) {
			uint8_t requested = tx_state;

			uart_line[uart_len] = '\0';
			switch (tx_parse_command(uart_line)) {
			case TX_CMD_SET_OBS:
				requested = STATE_OBSTACLE;
				break;
			case TX_CMD_SET_CLR:
				requested = STATE_CLEAR;
				break;
			default:
				/* Invalid input: ignore, keep state. */
				break;
			}

			tx_state_write(requested);
			uart_len = 0;
		}
	} else if (uart_len < sizeof(uart_line) - 1) {
		uart_line[uart_len++] = (char)byte;
	} else {
		/* Overlong line: discard, never match a tail. */
		uart_len = 0;
	}
}

static void transceiver_run(void)
{
	int64_t next_tx_pulse = k_uptime_get() + CONFIG_TRANSCEIVER_BLINK_INTERVAL_MS;
	int64_t activity_until = 0;

	for (;;) {
		int64_t now;

		if (role_switch_poll()) {
			role_switch_requested();
			next_tx_pulse = k_uptime_get() +
					CONFIG_TRANSCEIVER_BLINK_INTERVAL_MS;
			activity_until = 0;
		}

		if (phy_switch_poll()) {
			switch_phy();
		}

		/* UART input is meaningful only in TX mode; RX never
		 * consumes serial bytes as commands. */
		if (mode.role == TR_ROLE_TX) {
			tx_poll_uart();
		}
		if (state_switch_poll() && mode.role == TR_ROLE_TX && transport_active) {
			tx_state_toggle();
		}

		now = k_uptime_get();
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
		(void)gpio_pin_set_dt(mode.role == TR_ROLE_TX ? &led0 : &led1,
				      transport_active && now < activity_until &&
			      (mode.role == TR_ROLE_RX || tx_state == STATE_OBSTACLE));

		k_sleep(K_MSEC(5));
	}
}

int main(void)
{
	int err;

	if (!device_is_ready(console)) {
		return -ENODEV;
	}

	err = leds_init();
	if (err) {
		return err;
	}

	err = buttons_init();
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
	role_leds_update();
	transceiver_run();

	return 0;
}
