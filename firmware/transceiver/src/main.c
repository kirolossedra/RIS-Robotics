/*
 * Shared RIS Transceiver firmware.
 *
 * TX: newline-delimited OBS/CLR on the board console -> repeated BLE state.
 * RX: BLE state transitions -> newline-delimited OBS/CLR on the board console.
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
#include <zephyr/sys/printk.h>

#define LED0_NODE DT_ALIAS(led0)
#define LED1_NODE DT_ALIAS(led1)

#if !DT_NODE_HAS_STATUS(LED0_NODE, okay)
#error "The selected board must provide the led0 devicetree alias"
#endif

#if defined(CONFIG_TRANSCEIVER_ROLE_TX) && !DT_NODE_HAS_STATUS(LED1_NODE, okay)
#error "The TX role requires the board-provided led1 devicetree alias"
#endif

#define STATE_CLEAR    0x00
#define STATE_OBSTACLE 0x01
#define PROTOCOL_VERSION 0x01

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
#if defined(CONFIG_TRANSCEIVER_ROLE_TX)
static const struct gpio_dt_spec led1 = GPIO_DT_SPEC_GET(LED1_NODE, gpios);
#endif

static const struct device *const console = DEVICE_DT_GET(DT_CHOSEN(zephyr_console));

static int leds_init(void)
{
	int err;

	if (!gpio_is_ready_dt(&led0)) {
		return -ENODEV;
	}

	err = gpio_pin_configure_dt(&led0, GPIO_OUTPUT_INACTIVE);
	if (err) {
		return err;
	}

#if defined(CONFIG_TRANSCEIVER_ROLE_TX)
	if (!gpio_is_ready_dt(&led1)) {
		return -ENODEV;
	}

	err = gpio_pin_configure_dt(&led1, GPIO_OUTPUT_INACTIVE);
	if (err) {
		return err;
	}
#endif

	return 0;
}

static void leds_toggle(void)
{
	(void)gpio_pin_toggle_dt(&led0);
#if defined(CONFIG_TRANSCEIVER_ROLE_TX)
	(void)gpio_pin_toggle_dt(&led1);
#endif
}

#if defined(CONFIG_TRANSCEIVER_ROLE_TX)

static struct bt_le_ext_adv *advertiser;

static int advertise_state(uint8_t state)
{
	const struct bt_data ad[] = {
		BT_DATA(BT_DATA_SVC_DATA128, service_data, sizeof(service_data)),
	};

	service_data[17] = state;
	return bt_le_ext_adv_set_data(advertiser, ad, ARRAY_SIZE(ad), NULL, 0);
}

static int tx_ble_start(void)
{
	const struct bt_le_adv_param params = BT_LE_ADV_PARAM_INIT(
		BT_LE_ADV_OPT_EXT_ADV |
		BT_LE_ADV_OPT_CODED |
		BT_LE_ADV_OPT_REQUIRE_S8_CODING,
		BT_GAP_ADV_FAST_INT_MIN_2,
		BT_GAP_ADV_FAST_INT_MAX_2,
		NULL);
	int err;

	err = bt_le_ext_adv_create(&params, NULL, &advertiser);
	if (err) {
		return err;
	}

	err = advertise_state(STATE_CLEAR);
	if (err) {
		return err;
	}

	return bt_le_ext_adv_start(advertiser, BT_LE_EXT_ADV_START_DEFAULT);
}

static void tx_run(void)
{
	char line[8];
	size_t length = 0;
	uint8_t state = STATE_CLEAR;
	int64_t next_blink = k_uptime_get() + CONFIG_TRANSCEIVER_BLINK_INTERVAL_MS;

	for (;;) {
		uint8_t byte;
		int err = uart_poll_in(console, &byte);

		if (err == 0) {
			if (byte == '\r' || byte == '\n') {
				if (length > 0) {
					line[length] = '\0';
					uint8_t requested = state;

					if (strcmp(line, "OBS") == 0) {
						requested = STATE_OBSTACLE;
					} else if (strcmp(line, "CLR") == 0) {
						requested = STATE_CLEAR;
					}

					if (requested != state && advertise_state(requested) == 0) {
						state = requested;
					}
					length = 0;
				}
			} else if (length < sizeof(line) - 1) {
				line[length++] = (char)byte;
			} else {
				length = 0;
			}
		}

		if (k_uptime_get() >= next_blink) {
			leds_toggle();
			next_blink = k_uptime_get() + CONFIG_TRANSCEIVER_BLINK_INTERVAL_MS;
		}

		k_sleep(K_MSEC(5));
	}
}

#else /* CONFIG_TRANSCEIVER_ROLE_RX */

static int8_t received_state = -1;

static bool parse_ad(struct bt_data *data, void *user_data)
{
	ARG_UNUSED(user_data);

	if (data->type != BT_DATA_SVC_DATA128 || data->data_len != sizeof(service_data)) {
		return true;
	}

	if (memcmp(data->data, service_data, 16) != 0 ||
	    data->data[16] != PROTOCOL_VERSION) {
		return true;
	}

	uint8_t state = data->data[17];

	if (state == STATE_OBSTACLE && received_state != STATE_OBSTACLE) {
		received_state = STATE_OBSTACLE;
		printk("OBS\n");
	} else if (state == STATE_CLEAR && received_state == STATE_OBSTACLE) {
		received_state = STATE_CLEAR;
		printk("CLR\n");
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

static int rx_ble_start(void)
{
	const struct bt_le_scan_param params = {
		.type = BT_LE_SCAN_TYPE_PASSIVE,
		.options = BT_LE_SCAN_OPT_CODED | BT_LE_SCAN_OPT_NO_1M,
		.interval = BT_GAP_SCAN_FAST_INTERVAL,
		.window = BT_GAP_SCAN_FAST_WINDOW,
	};

	bt_le_scan_cb_register(&scan_callbacks);
	return bt_le_scan_start(&params, NULL);
}

static void rx_run(void)
{
	for (;;) {
		leds_toggle();
		k_sleep(K_MSEC(CONFIG_TRANSCEIVER_BLINK_INTERVAL_MS));
	}
}

#endif /* CONFIG_TRANSCEIVER_ROLE_TX */

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

	err = bt_enable(NULL);
	if (err) {
		return err;
	}

#if defined(CONFIG_TRANSCEIVER_ROLE_TX)
	err = tx_ble_start();
	if (err) {
		return err;
	}
	tx_run();
#else
	err = rx_ble_start();
	if (err) {
		return err;
	}
	rx_run();
#endif

	return 0;
}
