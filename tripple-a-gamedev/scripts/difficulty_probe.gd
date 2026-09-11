extends SceneTree
## Difficulty telemetry for the /tripple-a-gamedev loop. Answers "too easy / too hard /
## unfair" with MEASURED numbers instead of a reviewer's impression of a still frame.
##
##   SEEDS=0xC0FFEE,1,2,3 MAXT=40000 MODES=campaign,endless \
##   JSON_OUT=/abs/out.json CALIB=/abs/calibration.json \
##       godot --headless --path <project> -s res://.aaa/difficulty_probe.gd
##
## THREE RULES THIS ENCODES, each one paid for by a real mistake in this project:
##
## 1. STEP THE SIM, NEVER AWAIT FRAMES. A frame-paced probe runs at 60 ticks/second;
##    stepping runs at ~7,000. The whole 60 s 2P torture suite fits in ~11 s. Awaiting
##    frames is how a 5-minute capture became the only way to see the back half.
##
## 2. MEDIAN, NEVER MEAN. "Sector 4 owns 48% of all deaths" was one trapped seed
##    dragging the mean; the median said it was ordinary. Every stat here is a median
##    across seeds, and the per-seed spread is printed so a rogue seed is visible
##    rather than averaged in.
##
## 3. A KNOCKDOWN COUNT FROM A SCRIPTED BOT DOES NOT MEASURE DIFFICULTY. It measures
##    the bot. This project lost a full session to that: a "wall" at sector 4 was an
##    open-loop aim that could not track a 20px disc, absorbing 6,200 ticks and 35 of
##    41 knockdowns against a code budget of 150-320. So every stage also reports
##    OFFENSE (player kills per 1000 ticks). Costly + fighting normally = real
##    pressure. Costly + collapsed offense = the instrument is blind there, and the
##    number is about the driver. The second kind is never tunable.
##
## Verdicts are deliberately named *_CANDIDATE. A bot cannot establish that a human
## finds something too hard, so nothing here states it outright — the loop must pair a
## candidate with a human anchor before it ships as a difficulty finding.

const OFFENSE_BLIND_FRAC := 0.45   # stage offense below this share of the run median = blind
const HARD_FACTOR := 2.5           # knockdowns this many x the median = costly outlier
const MIN_STAGE_TICKS := 240       # ignore stages the run only clipped through (4 s)
const FROZEN_TICKS := 600          # a mover that has not shifted a pixel in 10 s is stuck
# Archetypes that legitimately hold position (they shoot from a standoff). Everything else
# is a mover, and a mover at zero velocity for FROZEN_TICKS is a GAME defect.
# "broadcast" is a rally-AURA MAST — a stationary structure that never moves by design.
# It was missing here until 2026-07-30, and every endless wave that spawned one reported
# GAME_SOFTLOCK on a structure doing its job (waves kept advancing past it — the
# "softlock" advanced 8 -> 14 while the "frozen" mast sat at y=-308).
const STATIONARY_KINDS := ["sniper", "ghillie", "grenadier", "elite", "mg_nest", "pilot", "broadcast"]


func _init() -> void:
	var MainScript: Script = load("res://src/main.gd")
	var seeds: Array = []
	var seed_env := OS.get_environment("SEEDS")
	for s in (seed_env if not seed_env.is_empty() else "0xC0FFEE,1,2,3").split(","):
		s = s.strip_edges()
		if not s.is_empty():
			seeds.append(s.hex_to_int() if s.begins_with("0x") else int(s))
	var maxt: int = int(OS.get_environment("MAXT")) if OS.has_environment("MAXT") else 40000
	var modes_env := OS.get_environment("MODES")
	var modes: Array = (modes_env if not modes_env.is_empty() else "campaign,endless").split(",")

	var report := {"seeds": seeds, "max_ticks": maxt, "modes": {}}
	for mode in modes:
		mode = mode.strip_edges()
		if mode.is_empty():
			continue
		report["modes"][mode] = _measure_mode(MainScript, mode, seeds, maxt)

	_print_report(report)
	_diff_calibration(report)

	var out := OS.get_environment("JSON_OUT")
	if not out.is_empty():
		var f := FileAccess.open(out, FileAccess.WRITE)
		if f == null:
			push_error("difficulty_probe: cannot write JSON_OUT " + out)
		else:
			f.store_string(JSON.stringify(report, "  "))
			f.close()
			print("\nWROTE ", out)
	quit()


func _measure_mode(MainScript: Script, mode: String, seeds: Array, maxt: int) -> Dictionary:
	## One entry per stage, each holding the per-seed samples. Campaign stages are
	## sector bands (|y| / GATE_SPACING + 1); endless stages are wave numbers.
	var per_stage := {}        # stage -> {ticks:[], downs:[], kills:[], stalled:[]}
	var reached := []          # deepest stage each seed got to
	var finished := 0

	for sd in seeds:
		var sim := SimWorld.new(sd, 1, mode)
		# The run must not be able to END, or a hard stage truncates its own evidence
		# and reads as cheap. God mode here is auto-RESTORE, not invulnerability: the
		# bot really does go down, so knockdowns stay a real signal.
		sim.god_mode = true
		var p: Dictionary = sim.players[0]
		var ticks := {}
		var downs := {}
		var kills := {}
		var stalled := {}
		var frozen := {}          # stage -> peak count of movers stuck past FROZEN_TICKS
		var still_for := {}       # enemy identity -> consecutive ticks at the same position
		var last_deaths: int = p["deaths"]
		var best_y: int = p["y"]
		var deepest := 0
		var t := 0
		while t < maxt:
			var stage: int = sim.wave if mode == "endless" \
				else absi(sim.players[0]["y"]) / SimWorld.GATE_SPACING + 1
			sim.step([MainScript.demo_input(t, sim)] as Array[SimInput])
			p = sim.players[0]
			deepest = maxi(deepest, stage)
			ticks[stage] = int(ticks.get(stage, 0)) + 1
			# Offense, straight off the sim's own kill events — the discriminator that
			# separates "this stage is hard" from "the bot cannot shoot here".
			for ev in sim.events:
				if ev.get("t", "") == "kill":
					kills[stage] = int(kills.get(stage, 0)) + 1
			var d: int = p["deaths"]
			if d > last_deaths:
				downs[stage] = int(downs.get(stage, 0)) + (d - last_deaths)
				last_deaths = d
			# FROZEN MOVERS. A wedged enemy and a bot that cannot shoot produce the SAME
			# collapsed-offense signature, and calling both "instrument" tells the loop to
			# ignore a genuine softlock — in Endless a wedged hostile holds the wave open
			# forever, because the wave only advances when every hostile is dead. Velocity
			# separates them: the driver's aim being bad does not stop the enemy walking.
			var seen := {}
			for ei in sim.enemies.size():
				var e: Dictionary = sim.enemies[ei]
				if not e["alive"] or STATIONARY_KINDS.has(str(e.get("kind", ""))):
					continue
				# A SUBMERGED frogman is not a frozen mover — it is an ambush predator
				# holding position by design until the player crosses NOTICE_RADIUS (60px),
				# grenade-killable the whole time. Counted 2026-07-30 as ~43 "frozen" movers
				# across campaign stages 2-6, every one a pre-wake lurker >60px from the
				# player, in runs that finished 4/4 campaigns. A NON-submerged frogman at
				# zero velocity still counts — that IS the _advance_toward wedge class.
				if str(e.get("kind", "")) == "frogman" and e.get("submerged", false):
					continue
				# Identity by kind+spawn-ish slot is unreliable (the arrays compact on death),
				# so key on position-history instead: a mover that reoccupies the exact same
				# fixed-point cell tick after tick is the thing we are looking for.
				var key := "%s@%d,%d" % [str(e.get("kind", "")), e["x"], e["y"]]
				seen[key] = true
				still_for[key] = int(still_for.get(key, 0)) + 1
			var stuck := 0
			for k in seen:
				if int(still_for.get(k, 0)) >= FROZEN_TICKS:
					stuck += 1
			for k in still_for.keys():
				if not seen.has(k):
					still_for.erase(k)   # it moved (new cell) or died — reset its clock
			if stuck > int(frozen.get(stage, 0)):
				frozen[stage] = stuck
			if mode != "endless":
				# Northward progress only; a stage where nothing advances is where a
				# player is actually stuck, whatever the death count says.
				if p["y"] < best_y:
					best_y = p["y"]
				else:
					stalled[stage] = int(stalled.get(stage, 0)) + 1
			if sim.victory:
				finished += 1
				break
			t += 1
		reached.append(deepest)
		for st in ticks:
			if not per_stage.has(st):
				per_stage[st] = {"ticks": [], "downs": [], "kills": [], "stalled": [], "frozen": []}
			per_stage[st]["ticks"].append(int(ticks.get(st, 0)))
			per_stage[st]["downs"].append(int(downs.get(st, 0)))
			per_stage[st]["kills"].append(int(kills.get(st, 0)))
			per_stage[st]["stalled"].append(int(stalled.get(st, 0)))
			per_stage[st]["frozen"].append(int(frozen.get(st, 0)))

	return _summarise(per_stage, reached, finished, seeds.size(), maxt)


func _summarise(per_stage: Dictionary, reached: Array, finished: int, n_seeds: int, maxt: int) -> Dictionary:
	var stages := per_stage.keys()
	stages.sort()

	# Run-wide median offense is the yardstick the blind check is made against — an
	# absolute threshold would just encode how good today's bot is.
	var offenses := []
	var rows := []
	for st in stages:
		var s: Dictionary = per_stage[st]
		var mt: int = _median(s["ticks"])
		if mt < MIN_STAGE_TICKS:
			continue
		var off := float(_median(s["kills"])) * 1000.0 / float(maxi(1, mt))
		offenses.append(off)
		var stalled_med: int = _median(s["stalled"])
		rows.append({"stage": int(st), "ticks_med": mt, "downs_med": _median(s["downs"]),
			"kills_med": _median(s["kills"]), "stalled_med": stalled_med,
			"stall_pct": snappedf(float(stalled_med) * 100.0 / float(maxi(1, mt)), 0.1),
			"frozen_med": _median(s["frozen"]),
			"offense": snappedf(off, 0.1), "samples": s["ticks"].size(),
			"downs_spread": s["downs"], "ticks_spread": s["ticks"]})
	var med_off := _median_f(offenses)
	var med_downs := _median(_col(rows, "downs_med"))
	# Stall is judged RELATIVE to this run's own median, never against an absolute. The bot
	# weaves rather than marching straight, so 60-80% non-advancing ticks is its normal
	# resting state in campaign — an absolute "85% = stuck" cutoff would condemn the whole
	# mode. What is diagnostic is one stage stalling far more than its neighbours.
	var med_stall := _median_f(_colf(rows, "stall_pct"))
	for r in rows:
		r["stall_ratio"] = snappedf(float(r["stall_pct"]) / maxf(0.1, med_stall), 0.01)

	for r in rows:
		r["verdict"] = _verdict(r, med_off, med_downs)
	return {"stages": rows, "median_offense": snappedf(med_off, 0.1),
		"median_downs": med_downs, "deepest_reached": reached,
		"campaigns_finished": finished, "seeds": n_seeds,
		"plateau": _plateau(reached)}


func _verdict(r: Dictionary, med_off: float, med_downs: int) -> String:
	## Offense gate FIRST. A stage the driver cannot fight in produces a knockdown
	## count that says nothing about the game, and reading it as difficulty is the
	## single most expensive mistake this loop has made.
	# CHECKED FIRST, and it outranks every other reading. A frozen mover is a GAME defect
	# that happens to produce the instrument-blind signature: offense collapses because
	# there is something alive that cannot be fought, not because the driver cannot aim.
	# Mislabelling it tells the loop "do not tune this", which is how a wave-holding
	# softlock would have been filed as a bot artifact and ignored forever. Found by the
	# behaviour lens, 2026-07-26: a rusher wedged on a rock corner held an Endless wave for
	# 37,350 ticks, and 5 of 6 endless runs had a mover frozen 600+ ticks.
	if int(r.get("frozen_med", 0)) > 0:
		return "GAME_SOFTLOCK"
	if med_off > 0.0 and float(r["offense"]) < med_off * OFFENSE_BLIND_FRAC:
		return "INSTRUMENT_BLIND"
	# Second blind check, for the case a raw offense ratio alone misses. A stage that is
	# COSTLY while doing worse than this run's own median at BOTH jobs — killing and
	# advancing — is a driver failing there, not a fight tuned harder. Both signals must
	# agree and the stage must actually be costly, so this is "everything points one way",
	# not a threshold fitted to a stage I wanted flagged. Campaign only: endless does not
	# scroll, so its stall column is structurally zero and would false-positive everything.
	if float(r["stall_ratio"]) > 0.0 \
			and int(r["downs_med"]) > med_downs \
			and float(r["offense"]) < med_off \
			and float(r["stall_ratio"]) > 1.0:
		return "INSTRUMENT_BLIND"
	if int(r["downs_med"]) >= maxi(2, int(round(float(med_downs) * HARD_FACTOR))):
		return "TOO_HARD_CANDIDATE"
	if int(r["downs_med"]) == 0 and float(r["offense"]) >= med_off:
		return "TOO_EASY_CANDIDATE"
	return "FAIR"


func _plateau(reached: Array) -> int:
	## The deepest stage every seed got to. In endless this is the wave the driver
	## stops advancing at — a hard ceiling is far more interesting than an average.
	if reached.is_empty():
		return 0
	var m: int = reached[0]
	for r in reached:
		m = mini(m, int(r))
	return m


func _print_report(report: Dictionary) -> void:
	for mode in report["modes"]:
		var m: Dictionary = report["modes"][mode]
		print("\n=== %s — %d seeds, median offense %.1f kills/1000t, floor stage %d"
			% [mode.to_upper(), m["seeds"], m["median_offense"], m["plateau"]])
		print("  stage  ticks   downs  kills  offense  stall%   vs.med  froze  verdict")
		for r in m["stages"]:
			print("  %-6d %-7d %-6d %-6d %-8.1f %-7.1f %-7.2f %-6d %s"
				% [r["stage"], r["ticks_med"], r["downs_med"], r["kills_med"],
					r["offense"], r["stall_pct"], r["stall_ratio"],
					r.get("frozen_med", 0), r["verdict"]])
		if mode != "endless":
			print("  campaigns finished: %d/%d" % [m["campaigns_finished"], m["seeds"]])
		var blind := []
		var locked := []
		for r in m["stages"]:
			if r["verdict"] == "INSTRUMENT_BLIND":
				blind.append("s%d" % r["stage"])
			elif r["verdict"] == "GAME_SOFTLOCK":
				locked.append("s%d (%d frozen)" % [r["stage"], int(r.get("frozen_med", 0))])
		if not blind.is_empty():
			print("  ⚠ %s measure the DRIVER, not the game — do not tune on them."
				% ", ".join(blind))
		if not locked.is_empty():
			print("  🛑 %s held a live mover at ZERO velocity past %d ticks. This is a GAME"
				% [", ".join(locked), FROZEN_TICKS])
			print("     defect, NOT an instrument artifact — it looks identical in the offense")
			print("     column, so it must be read here. In Endless a frozen hostile holds the")
			print("     wave open forever, because the wave advances only when all are dead.")


func _diff_calibration(report: Dictionary) -> void:
	## The only difficulty signal that does not depend on how good the driver is: the
	## DELTA against the last recorded measurement. Same bot, same seeds, different
	## number => the GAME moved. An absolute "too hard" from a bot is unanchored.
	var path := OS.get_environment("CALIB")
	if path.is_empty() or not FileAccess.file_exists(path):
		print("\n(no calibration baseline — this run becomes the baseline)")
		return
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return
	var prev = JSON.parse_string(f.get_as_text())
	f.close()
	if typeof(prev) != TYPE_DICTIONARY or not prev.has("modes"):
		print("\n(calibration file unreadable — ignoring)")
		return
	print("\n=== DELTA vs calibration recorded %s" % prev.get("recorded", "?"))
	var moved := false
	for mode in report["modes"]:
		if not prev["modes"].has(mode):
			continue
		var old_by := {}
		for r in prev["modes"][mode].get("stages", []):
			old_by[int(r["stage"])] = r
		for r in report["modes"][mode]["stages"]:
			var o = old_by.get(int(r["stage"]), null)
			if o == null:
				print("  %s s%d  NEW stage (no baseline)" % [mode, r["stage"]])
				moved = true
				continue
			var dd: int = int(r["downs_med"]) - int(o["downs_med"])
			var dt: int = int(r["ticks_med"]) - int(o["ticks_med"])
			if absi(dd) >= 2 or absf(float(dt)) >= float(maxi(1, int(o["ticks_med"]))) * 0.25:
				print("  %s s%d  downs %d -> %d (%+d)   ticks %d -> %d (%+d)"
					% [mode, r["stage"], o["downs_med"], r["downs_med"], dd,
						o["ticks_med"], r["ticks_med"], dt])
				moved = true
	if not moved:
		print("  no stage moved materially — the curve is where it was.")


func _col(rows: Array, key: String) -> Array:
	var out := []
	for r in rows:
		out.append(int(r[key]))
	return out


func _colf(rows: Array, key: String) -> Array:
	var out := []
	for r in rows:
		out.append(float(r[key]))
	return out


func _median(a: Array) -> int:
	if a.is_empty():
		return 0
	var s := a.duplicate()
	s.sort()
	return int(s[s.size() / 2])


func _median_f(a: Array) -> float:
	if a.is_empty():
		return 0.0
	var s := a.duplicate()
	s.sort()
	return float(s[s.size() / 2])
