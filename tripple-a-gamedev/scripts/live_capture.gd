extends SceneTree
## Capture frames from a REAL run, not from hand-posed sim states.
##
##   SHOT_DIR=/abs/path godot --path <project> --rendering-method gl_compatibility \
##       -s res://.aaa/live_capture.gd
##
## Why this exists: the posed harness (tools/screenshots.gd) builds sim states by hand, and
## a field it forgets to pose renders as a BUG. Observed live — the victory card was captured
## boasting "SCORE 264,500 / 0 KILLS / BANKED 0" because the shot builder set score and never
## touched the kill counter. A blind reviewer correctly called that a broken results screen,
## and a whole plan/code/gate cycle went to "fixing" perfectly good code. Frames taken from a
## run that actually happened cannot lie that way: every number on screen was earned.
##
## It also captures what a still of a frozen pose never can — mid-combat fx, banners firing on
## their own schedule, deaths, respawns, wave transitions.
##
## Optional env:
##   SHOT_DIR    where to write (default /tmp)
##   LIVE_FRAMES total frames to run (default 900 = ~15 s)
##   LIVE_EVERY  capture every Nth frame (default 60)
##   LIVE_MODE   "campaign" (default) or "endless"
##   LIVE_GOD    "1" to run the DEBUG-ONLY god mode (auto-restore, not invulnerability). The bot
##               still gets killed — it just gets put back on its feet once a second — so the run
##               cannot END and the capture finally reaches the back half of the game. Without it
##               nothing has ever screenshotted sectors 3-6, the Colossus, or the victory card.
##               Prints KNOCKDOWNS per sector on the way out: the first real difficulty telemetry
##               this game has had, and the thing invulnerability could never have reported.

var main: Node2D
var out_dir := "/tmp"
var total := 900
var every := 60
var shot := 0


func _initialize() -> void:
	out_dir = OS.get_environment("SHOT_DIR")
	if out_dir.is_empty():
		out_dir = "/tmp"
	var f := OS.get_environment("LIVE_FRAMES")
	if f.is_valid_int():
		total = maxi(60, int(f))
	var e := OS.get_environment("LIVE_EVERY")
	if e.is_valid_int():
		every = maxi(2, int(e))
	main = (load("res://src/main.tscn") as PackedScene).instantiate()
	root.add_child(main)
	# The harness window never holds focus; without this every frame is a pause overlay.
	main.no_autopause = true
	_run()


func _run() -> void:
	# main._ready() runs on the first process step, so nothing below may touch main's
	# lazily-built children until at least one frame has been drawn.
	await RenderingServer.frame_post_draw
	_kill_splash()
	# Start a real run. start_game() is the same entry the TITLE row uses.
	# start_game(endless: bool) — the same entry the TITLE rows use.
	main.start_game(OS.get_environment("LIVE_MODE") == "endless")
	# Nobody is holding a controller. Without this the "live" run is a soldier standing
	# still at sector 1, dying and respawning until the frame budget runs out — which is
	# what every capture before 2026-07-25 actually showed the reviewer. demo_autoplay
	# hands the sim main.gd's scripted bot (marches north, fires, grenades, takes tanks).
	main.demo_autoplay = true
	# DEBUG-ONLY. main._physics_process re-asserts OS.is_debug_build() before every step, so this
	# is inert in an exported build; here it just stops the run ending at the first sector.
	var god := OS.get_environment("LIVE_GOD") == "1"
	main.god_mode = god
	var start_m := -Fixed.to_int(main.sim.camera_top) / 10
	# Knockdowns per sector. p["deaths"] keeps counting under god mode (the bot really does die),
	# so this is read straight off the sim rather than inferred from the pixels.
	var downs_by_sector := {}
	var last_deaths := 0
	var frame := 0
	while frame < total:
		await RenderingServer.frame_post_draw
		frame += 1
		_kill_splash()   # a mid-run restart can re-arm it
		var deaths := 0
		for p in main.sim.players:
			deaths += int(p["deaths"])
		if deaths > last_deaths:
			var sec: int = main.sim._gate_counter + 1
			downs_by_sector[sec] = int(downs_by_sector.get(sec, 0)) + (deaths - last_deaths)
			last_deaths = deaths
		if frame % every == 0:
			var img := root.get_texture().get_image()
			shot += 1
			var path := "%s/%02d-live-t%04d.png" % [out_dir, shot, frame]
			if img.save_png(path) != OK:
				push_error("live_capture: save_png failed for " + path + " — does SHOT_DIR exist?")
				print("FAILED ", path)
			else:
				print("SAVED ", path)
	# Liveness, measured from the sim rather than guessed from the pixels: a capture is
	# only worth reviewing if the run actually went somewhere. Floors are calibrated on
	# real runs of this harness — an INPUT-LESS run (the bug this replaced) manages ~5m
	# and ~590 pts per 1000 frames; a played one does ~39m and ~3300.
	var metres := -Fixed.to_int(main.sim.camera_top) / 10 - start_m
	var scored: int = main.sim.score
	var per_k := float(total) / 1000.0
	print("PROGRESS %dm advanced, %d pts, sector gate %d, over %d frames"
		% [metres, scored, main.sim._gate_counter, total])
	var secs := downs_by_sector.keys()
	secs.sort()
	var per := []
	for s in secs:
		per.append("s%d=%d" % [s, downs_by_sector[s]])
	print("KNOCKDOWNS %d total (%s)" % [last_deaths, ", ".join(per) if not per.is_empty() else "none"])
	print("ENDSTATE victory=%s wiped=%s last_stand=%s god=%s"
		% [main.sim.victory, main.sim.wiped, main.sim.last_stand, god])
	if god:
		# The stagnation floors below are calibrated on a run that ENDS at sector 1-2. A god run
		# is expected to blow straight past them, so a failure here would only ever be noise.
		print("ALL SHOTS DONE")
		quit(0)
		return
	if metres < int(15.0 * per_k) or scored < int(1000.0 * per_k):
		push_error("live_capture: the run barely moved (%dm, %d pts over %d frames) — these frames "
			% [metres, scored, total]
			+ "show a soldier standing still, not gameplay. Is main.demo_autoplay still honoured?")
		print("CAPTURE STAGNANT")
		quit(1)
		return   # quit() only requests a quit; without this the quit(0) below overrides it
	print("ALL SHOTS DONE")
	quit(0)


func _kill_splash() -> void:
	## The boot splash paints over the whole frame for its first seconds. Left alone it
	## eats the opening captures — every early shot comes back as the studio card.
	if main == null:
		return
	main._splash_t = 0.0
	if main._splash_layer != null:
		main._splash_layer.visible = false
