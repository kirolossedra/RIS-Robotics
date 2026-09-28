/*
 * Shared RIS Transceiver protocol helpers.
 *
 * Pure state-machine logic with no Zephyr dependencies so the same code
 * runs in firmware (src/main.c) and in a host-side unit test
 * (tests/test_protocol.c).
 *
 * Wire/state values:
 *   STATE_CLEAR    (0x00) = obstacle condition cleared
 *   STATE_OBSTACLE (0x01) = obstacle condition active
 * Any other state byte is malformed and must never become OBS or CLR.
 */

#ifndef TRANSCEIVER_PROTOCOL_H
#define TRANSCEIVER_PROTOCOL_H

#include <stdbool.h>
#include <stdint.h>
#include <string.h>

#define TRANSCEIVER_STATE_CLEAR    ((uint8_t)0x00)
#define TRANSCEIVER_STATE_OBSTACLE ((uint8_t)0x01)

/* RX deduplication epoch before the first valid packet. */
#define TRANSCEIVER_RX_UNKNOWN ((int8_t)-1)

/* Outcome of parsing one newline-delimited host console line on TX. */
enum tx_cmd_action {
	TX_CMD_IGNORE = 0,
	TX_CMD_SET_OBS,
	TX_CMD_SET_CLR,
};

/*
 * Map an exact host command line to an action. Only the exact strings
 * "OBS" and "CLR" act; NULL, empty, wrong-case, padded, overlong, or
 * otherwise invalid input is explicitly ignored (never coerced to a state).
 */
static inline enum tx_cmd_action tx_parse_command(const char *line)
{
	if (line == NULL) {
		return TX_CMD_IGNORE;
	}
	if (strcmp(line, "OBS") == 0) {
		return TX_CMD_SET_OBS;
	}
	if (strcmp(line, "CLR") == 0) {
		return TX_CMD_SET_CLR;
	}
	return TX_CMD_IGNORE;
}

/* Outcome of feeding one validated BLE state byte into the RX dedup. */
enum rx_emit {
	RX_EMIT_NONE = 0,
	RX_EMIT_OBS,
	RX_EMIT_CLR,
};

/*
 * Deduplicate repeated BLE state broadcasts.
 *
 * Rules (ble-runtime-0002, preserved):
 * - First OBS after unknown/CLR  -> emit OBS once.
 * - Repeated OBS while OBS        -> silent.
 * - First CLR after OBS           -> emit CLR once.
 * - Repeated CLR / CLR from
 *   unknown (startup)             -> silent.
 * - Malformed state byte          -> silent, dedup state unchanged.
 *
 * Returns what the host console must emit; *current always holds the last
 * accepted logical state (or TRANSCEIVER_RX_UNKNOWN).
 */
static inline enum rx_emit rx_dedup_update(int8_t *current, uint8_t incoming)
{
	int8_t prev;

	if (current == NULL) {
		return RX_EMIT_NONE;
	}
	prev = *current;

	if (incoming == TRANSCEIVER_STATE_OBSTACLE) {
		if (prev != (int8_t)TRANSCEIVER_STATE_OBSTACLE) {
			*current = (int8_t)TRANSCEIVER_STATE_OBSTACLE;
			return RX_EMIT_OBS;
		}
		return RX_EMIT_NONE;
	}

	if (incoming == TRANSCEIVER_STATE_CLEAR) {
		if (prev == (int8_t)TRANSCEIVER_STATE_OBSTACLE) {
			*current = (int8_t)TRANSCEIVER_STATE_CLEAR;
			return RX_EMIT_CLR;
		}
		return RX_EMIT_NONE;
	}

	return RX_EMIT_NONE;
}

/*
 * Runtime operating mode (ble-runtime-0004): ONE firmware image performs either side
 * of the protocol. Role (TX/RX) and PHY (Coded S=8 / 1M) are independent
 * dimensions toggled by two separate physical buttons.
 *
 * Rules:
 * - Boot default is TX + Coded S=8.
 * - The role button toggles role and preserves PHY.
 * - The PHY button toggles PHY and preserves role.
 * - All four combinations are reachable from any state.
 * - Repeated presses alternate deterministically.
 */
enum tr_role {
	TR_ROLE_TX = 0,
	TR_ROLE_RX = 1,
};

enum tr_phy {
	TR_PHY_CODED_S8 = 0,
	TR_PHY_1M = 1,
};

#define TR_BOOT_ROLE TR_ROLE_TX
#define TR_BOOT_PHY  TR_PHY_CODED_S8

struct tr_mode {
	enum tr_role role;
	enum tr_phy phy;
};

static inline enum tr_role tr_role_toggled(enum tr_role role)
{
	return (role == TR_ROLE_TX) ? TR_ROLE_RX : TR_ROLE_TX;
}

static inline enum tr_phy tr_phy_toggled(enum tr_phy phy)
{
	return (phy == TR_PHY_CODED_S8) ? TR_PHY_1M : TR_PHY_CODED_S8;
}

/* Role button (Button 2): switch TX<->RX, keep the current PHY. */
static inline void tr_press_role_button(struct tr_mode *mode)
{
	if (mode != NULL) {
		mode->role = tr_role_toggled(mode->role);
	}
}

/* PHY button (Button 1): switch S=8<->1M, keep the current role. */
static inline void tr_press_phy_button(struct tr_mode *mode)
{
	if (mode != NULL) {
		mode->phy = tr_phy_toggled(mode->phy);
	}
}

#endif /* TRANSCEIVER_PROTOCOL_H */
