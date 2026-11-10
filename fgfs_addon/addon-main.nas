# WinWing MCDU bridge add-on.
# It exports the A320-family MCDU screen to properties and runs the keys sent by the Python bridge.

var TEXT_IDS = ["Scratchpad", "Simple_C1", "Simple_C2", "Simple_C3", "Simple_C4", "Simple_C5", "Simple_C6", "Simple_C1S", "Simple_C2S", "Simple_C3S", "Simple_C4S", "Simple_C5S", "Simple_C6S", "Simple_C3B", "Simple_C4B", "Simple_Title2", "Simple_Title", "Simple_PageNum", "Simple_L1", "Simple_L2", "Simple_L3", "Simple_L4", "Simple_L5", "Simple_L6", "Simple_L1S", "Simple_L2S", "Simple_L3S", "Simple_L4S", "Simple_L5S", "Simple_L6S", "Simple_R1", "Simple_R2", "Simple_R3", "Simple_R4", "Simple_R5", "Simple_R6", "Simple_R1S", "Simple_R2S", "Simple_R3S", "Simple_R4S", "Simple_R5S", "Simple_R6S", "Simple_L0S", "FPLN_Callsign", "FPLN_TMPY", "text3623", "text3627", "text3729", "text3725", "FPLN_FROM", "text174", "text178", "text191", "text195", "text4290", "text4470", "INITB_ZFWCG_S", "text4372", "text4322", "text4380", "text4392", "FUELPRED_ZFWCG_S", "text1056", "text1060", "text1081", "PERFTO_F", "PERFTO_S", "PERFTO_O", "PERFTO_FE", "PERFTO_SE", "PERFTO_OE", "PERFAPPR_F", "PERFAPPR_S", "PERFAPPR_O", "PERFAPPR_FE", "PERFAPPR_SE", "PERFAPPR_OE", "PERFGA_F", "PERFGA_S", "PERFGA_O", "PERFGA_FE", "PERFGA_SE", "PERFGA_OE"];
var OVERLAY_IDS = ["ArrowLeft", "ArrowRight", "Simple_L1_Arrow", "Simple_L2_Arrow", "Simple_L3_Arrow", "Simple_L4_Arrow", "Simple_L5_Arrow", "Simple_L6_Arrow", "Simple_R1_Arrow", "Simple_R2_Arrow", "Simple_R3_Arrow", "Simple_R4_Arrow", "Simple_R5_Arrow", "Simple_R6_Arrow", "g4241", "g4324", "g186", "g205", "arrow5L", "arrow4L", "arrow3L", "arrow2L", "arrow1L", "arrow5R", "arrow4R", "arrow3R", "arrow2R", "arrow1R", "INITA_AlignIRS", "INITA_InitRequest", "g4304", "g4310", "INITA_CoRoute", "INITA_FltNbr", "INITA_CostIndex", "INITA_CruiseFLTemp", "IRSINIT_up_1", "IRSINIT_down_2", "IRSINIT_up_1-8", "IRSINIT_down_2-7", "IRSINIT_star", "g3590", "g3595", "g4400", "g1068", "g1077", "WIND_CANCEL", "WIND_INSERT_star", "WIND_up", "WIND_down", "PERFTO_TOSHIFT", "PERFTO_V1", "PERFTO_VR", "PERFTO_V2", "PERFAPPR_LDG_3", "PERFAPPR_LDG_F", "PROG_UPDATE", "NOTIFY", "NOTIFY_FLTNBR", "NOTIFY_AIRPORT", "COCALL", "COCALLTUNE", "COMM-ADS", "PRINTPAGE", "MODEVHF3", "WEATHERREQSEND", "ATISSend1", "ATISSend2", "ATISSend4", "ATISSend3", "g1338", "g1346"];
var UPDATE_SECONDS = 0.2;
var ROOT = "/mcdu-bridge";
var ALLOWED = {button: 1, lskbutton: 1, rskbutton: 1, pagebutton: 1, arrowbutton: 1};
var POWER_BUS = ["/systems/electrical/bus/ac-1", "/systems/electrical/bus/ac-2"];
var POWER_MIN = 110;
var cache = [{source: nil, items: []}, {source: nil, items: []}];
var timer = nil;
var key_listener = nil;

# Get the aircraft MCDU object for one side, or nil when it does not exist.
var get_mcdu = func(unit) {
    if (!contains(globals, "canvas_mcdu")) return nil;
    var name = unit == 0 ? "MCDU_1" : "MCDU_2";
    if (!contains(globals["canvas_mcdu"], name)) return nil;
    return globals["canvas_mcdu"][name];
};

# Collect the canvas elements of one MCDU only once.
var build_cache = func(unit, source) {
    var items = [];
    var missing = 0;
    foreach (var id; TEXT_IDS) {
        var element = source.page.getElementById(id);
        if (element == nil) missing += 1;
        else append(items, {id: id, node: element._node, is_text: 1});
    }
    foreach (var id; OVERLAY_IDS) {
        var element = source.page.getElementById(id);
        if (element == nil) missing += 1;
        else append(items, {id: id, node: element._node, is_text: 0});
    }
    cache[unit].source = source;
    cache[unit].items = items;
    setprop(ROOT ~ "/missing-elements", missing);
};

# Check this element and all its parents.
var is_visible = func(node) {
    while (node != nil and node.getName() != "texture") {
        var visible = node.getNode("visible");
        if (visible != nil and !visible.getBoolValue()) return 0;
        node = node.getParent();
    }
    return 1;
};

# Read a text value from a child property.
var read_text = func(node, name) {
    var child = node.getNode(name);
    if (child == nil) return "";
    var value = child.getValue();
    return value == nil ? "" : value ~ "";
};

# Find the color of the first path inside a group.
var overlay_color = func(node) {
    foreach (var path; node.getChildren("path")) {
        var color = read_text(path, "stroke");
        if (color == "" or color == "none") color = read_text(path, "fill");
        if (color != "" and color != "none") return color;
    }
    foreach (var group; node.getChildren("group")) {
        var color = overlay_color(group);
        if (color != "") return color;
    }
    return "";
};

# Write the visible elements of one MCDU as one text property.
var export_unit = func(unit, source) {
    if (cache[unit].source != source) build_cache(unit, source);
    var output = "";
    foreach (var item; cache[unit].items) {
        if (!is_visible(item.node)) continue;
        if (item.is_text) {
            var text = read_text(item.node, "text");
            if (text != "") output ~= item.id ~ "\t" ~ text ~ "\t" ~ read_text(item.node, "fill") ~ "\t" ~ read_text(item.node, "character-size") ~ "\n";
        } else {
            output ~= item.id ~ "\t\t" ~ overlay_color(item.node) ~ "\t0\n";
        }
    }
    setprop(ROOT ~ "/unit" ~ unit, output);
};

# Update both screens and the status.
var update = func {
    if (!contains(globals, "canvas_mcdu") or !contains(globals, "mcdu")) {
        setprop(ROOT ~ "/status", getprop("/sim/signals/fdm-initialized") ? "no-mcdu" : "loading");
        return;
    }
    var left = get_mcdu(0);
    var right = get_mcdu(1);
    if (left == nil or right == nil) {
        setprop(ROOT ~ "/status", "loading");
        return;
    }
    export_unit(0, left);
    export_unit(1, right);
    setprop(ROOT ~ "/status", "ready");
};

# Run a key sent by the bridge. Format: side|function|key|event.
var handle_key = func(node) {
    var parts = split("|", node.getValue());
    if (size(parts) != 4 or !contains(ALLOWED, parts[1]) or !contains(globals, "mcdu")) return;
    var unit = num(parts[0]);
    if (unit != 0 and unit != 1) return;
    var power = getprop(POWER_BUS[unit]);
    if (power == nil or power < POWER_MIN) return;
    var arguments = parts[3] == "none" ? [parts[2], unit] : [parts[2], unit, parts[3]];
    var errors = [];
    call(globals["mcdu"][parts[1]], arguments, nil, nil, errors);
    if (size(errors) > 0) print("MCDU bridge key error: " ~ errors[0]);
};

# Start the add-on.
var main = func(addon) {
    props.globals.initNode(ROOT ~ "/status", "loading", "STRING");
    props.globals.initNode(ROOT ~ "/unit0", "", "STRING");
    props.globals.initNode(ROOT ~ "/unit1", "", "STRING");
    props.globals.initNode(ROOT ~ "/key-input", "", "STRING");
    props.globals.initNode(ROOT ~ "/missing-elements", 0, "INT");
    key_listener = setlistener(ROOT ~ "/key-input", handle_key, 0, 1);
    timer = maketimer(UPDATE_SECONDS, update);
    timer.start();
    print("MCDU bridge add-on loaded");
};

# Stop the add-on.
var unload = func(addon) {
    if (timer != nil) timer.stop();
    if (key_listener != nil) removelistener(key_listener);
};
