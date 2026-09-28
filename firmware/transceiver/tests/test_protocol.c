/*
 * Host-side unit test for the shared Transceiver protocol helpers.
 *
 * Builds and runs on any host C compiler (no Zephyr dependency):
 *
 *   cc -Wall -Wextra -std=c99 -o test_protocol test_protocol.c && ./test_protocol
 *
 * Requires two physical nRF52833 DKs for radio validation, so this test
 * covers only the pure state-machine logic: TX command parsing and RX
 * duplicate suppression / state transitions.
 */

#include <assert.h>
#include <stdint.h>
#include <stdio.h>

#include "../src/protocol.h"

static int checks;

#define CHECK(cond)                                                            \
	do {                                                                   \
		checks++;                                                      \
		if (!(cond)) {                                                 \
			printf("FAIL %s:%d: %s\n", __FILE__, __LINE__,      \
			       #cond);                                         \
			return 1;                                              \
		}                                                              \
	} while (0)

static int test_tx_parse(void)
{
	CHECK(tx_parse_command("OBS") == TX_CMD_SET_OBS);
	CHECK(tx_parse_command("CLR") == TX_CMD_SET_CLR);

	/* Everything else is explicitly ignored, never coerced. */
	CHECK(tx_parse_command("") == TX_CMD_IGNORE);
	CHECK(tx_parse_command("obs") == TX_CMD_IGNORE);
	CHECK(tx_parse_command("clr") == TX_CMD_IGNORE);
	CHECK(tx_parse_command("OBS ") == TX_CMD_IGNORE);
	CHECK(tx_parse_command(" OBS") == TX_CMD_IGNORE);
	CHECK(tx_parse_command("OB") == TX_CMD_IGNORE);
	CHECK(tx_parse_command("OBSS") == TX_CMD_IGNORE);
	CHECK(tx_parse_command("CLEAR") == TX_CMD_IGNORE);
	CHECK(tx_parse_command("OBSTACLE") == TX_CMD_IGNORE);
	CHECK(tx_parse_command("ERR adv-restart") == TX_CMD_IGNORE);
	CHECK(tx_parse_command(NULL) == TX_CMD_IGNORE);
	return 0;
}

static int test_rx_dedup(void)
{
	int8_t current = TRANSCEIVER_RX_UNKNOWN;

	/* Startup CLR is silent: an episode starts with the first OBS. */
	CHECK(rx_dedup_update(&current, TRANSCEIVER_STATE_CLEAR) ==
	      RX_EMIT_NONE);
	CHECK(current == TRANSCEIVER_RX_UNKNOWN);

	/* First OBS emits once; repeats are silent. */
	CHECK(rx_dedup_update(&current, TRANSCEIVER_STATE_OBSTACLE) ==
	      RX_EMIT_OBS);
	CHECK(current == (int8_t)TRANSCEIVER_STATE_OBSTACLE);
	CHECK(rx_dedup_update(&current, TRANSCEIVER_STATE_OBSTACLE) ==
	      RX_EMIT_NONE);
	CHECK(rx_dedup_update(&current, TRANSCEIVER_STATE_OBSTACLE) ==
	      RX_EMIT_NONE);

	/* Malformed bytes never emit and never disturb the dedup state. */
	CHECK(rx_dedup_update(&current, 0x02) == RX_EMIT_NONE);
	CHECK(current == (int8_t)TRANSCEIVER_STATE_OBSTACLE);
	CHECK(rx_dedup_update(&current, 0xFF) == RX_EMIT_NONE);
	CHECK(current == (int8_t)TRANSCEIVER_STATE_OBSTACLE);

	/* First CLR after OBS emits once; repeats are silent. */
	CHECK(rx_dedup_update(&current, TRANSCEIVER_STATE_CLEAR) ==
	      RX_EMIT_CLR);
	CHECK(current == (int8_t)TRANSCEIVER_STATE_CLEAR);
	CHECK(rx_dedup_update(&current, TRANSCEIVER_STATE_CLEAR) ==
	      RX_EMIT_NONE);

	/* A new episode emits OBS again. */
	CHECK(rx_dedup_update(&current, TRANSCEIVER_STATE_OBSTACLE) ==
	      RX_EMIT_OBS);
	return 0;
}

static int test_rx_episode_sequence(void)
{
	/* wireless: OBS OBS OBS OBS CLR CLR CLR OBS OBS
	 * serial:   OBS             CLR         OBS        (README contract)
	 */
	static const uint8_t wireless[] = {1, 1, 1, 1, 0, 0, 0, 1, 1};
	static const int expected[] = {1, 0, 0, 0, 2, 0, 0, 1, 0};
	int8_t current = TRANSCEIVER_RX_UNKNOWN;
	size_t i;

	for (i = 0; i < sizeof(wireless); i++) {
		enum rx_emit emit =
			rx_dedup_update(&current, wireless[i]);

		CHECK((int)emit == expected[i]);
	}
	return 0;
}

static int test_rx_null_guard(void)
{
	CHECK(rx_dedup_update(NULL, TRANSCEIVER_STATE_OBSTACLE) ==
	      RX_EMIT_NONE);
	return 0;
}

static int test_boot_defaults(void)
{
	/* Deterministic boot: TX + Coded S=8 (ble-runtime-0004). */
	CHECK(TR_BOOT_ROLE == TR_ROLE_TX);
	CHECK(TR_BOOT_PHY == TR_PHY_CODED_S8);
	return 0;
}

static int test_role_transitions(void)
{
	struct tr_mode mode = { TR_BOOT_ROLE, TR_BOOT_PHY };

	/* TX -> RX -> TX -> RX: repeated presses toggle deterministically. */
	tr_press_role_button(&mode);
	CHECK(mode.role == TR_ROLE_RX);
	tr_press_role_button(&mode);
	CHECK(mode.role == TR_ROLE_TX);
	tr_press_role_button(&mode);
	CHECK(mode.role == TR_ROLE_RX);
	tr_press_role_button(NULL); /* NULL is a safe no-op. */
	CHECK(mode.role == TR_ROLE_RX);
	return 0;
}

static int test_phy_role_independence(void)
{
	struct tr_mode mode = { TR_BOOT_ROLE, TR_BOOT_PHY };
	int seen[2][2] = { { 0, 0 }, { 0, 0 } };
	int i;

	/* Walk roles and PHYs; every combination must be reachable and a
	 * switch on one dimension must preserve the other. */
	for (i = 0; i < 8; i++) {
		seen[mode.role][mode.phy] = 1;
		if (i % 2 == 0) {
			enum tr_phy before = mode.phy;

			tr_press_role_button(&mode);
			CHECK(mode.phy == before);
		} else {
			enum tr_role before = mode.role;

			tr_press_phy_button(&mode);
			CHECK(mode.role == before);
		}
	}
	seen[mode.role][mode.phy] = 1;

	CHECK(seen[TR_ROLE_TX][TR_PHY_CODED_S8]);
	CHECK(seen[TR_ROLE_TX][TR_PHY_1M]);
	CHECK(seen[TR_ROLE_RX][TR_PHY_CODED_S8]);
	CHECK(seen[TR_ROLE_RX][TR_PHY_1M]);

	/* Explicit orthogonality examples from the system contract. */
	mode.role = TR_ROLE_TX;
	mode.phy = TR_PHY_CODED_S8;
	tr_press_role_button(&mode); /* TX+S=8 -> RX+S=8 */
	CHECK(mode.role == TR_ROLE_RX && mode.phy == TR_PHY_CODED_S8);
	tr_press_phy_button(&mode); /* RX+S=8 -> RX+1M */
	CHECK(mode.role == TR_ROLE_RX && mode.phy == TR_PHY_1M);
	tr_press_role_button(&mode); /* RX+1M -> TX+1M */
	CHECK(mode.role == TR_ROLE_TX && mode.phy == TR_PHY_1M);
	tr_press_phy_button(NULL); /* NULL is a safe no-op. */
	return 0;
}

int main(void)
{
	if (test_tx_parse() != 0) {
		return 1;
	}
	if (test_rx_dedup() != 0) {
		return 1;
	}
	if (test_rx_episode_sequence() != 0) {
		return 1;
	}
	if (test_rx_null_guard() != 0) {
		return 1;
	}
	if (test_boot_defaults() != 0) {
		return 1;
	}
	if (test_role_transitions() != 0) {
		return 1;
	}
	if (test_phy_role_independence() != 0) {
		return 1;
	}
	printf("PASS: %d protocol checks\n", checks);
	return 0;
}
