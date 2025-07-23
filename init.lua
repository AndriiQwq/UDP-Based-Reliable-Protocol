local myprotocol = Proto("myprotocol", "My Protocol")

local sequence_number = ProtoField.uint32("myprotocol.sequence_number", "Sequence Number", base.DEC)
local acknowledgement = ProtoField.uint32("myprotocol.acknowledgement", "Acknowledgement", base.DEC)
local flags = ProtoField.uint8("myprotocol.flags", "Flags", base.HEX)
local window = ProtoField.uint16("myprotocol.window", "Window Size", base.DEC)
local checksum = ProtoField.uint16("myprotocol.checksum", "Checksum", base.HEX)
local data = ProtoField.bytes("myprotocol.data", "Data")

local flag_1 = ProtoField.bool("myprotocol.flag1", "Flag 1")
local flag_2 = ProtoField.bool("myprotocol.flag2", "Flag 2")
local flag_3 = ProtoField.bool("myprotocol.flag3", "Flag 3")
local flag_4 = ProtoField.bool("myprotocol.flag4", "Flag 4")
local flag_5 = ProtoField.bool("myprotocol.flag5", "Flag 5")
local flag_6 = ProtoField.bool("myprotocol.flag6", "Flag 6")
local flag_7 = ProtoField.bool("myprotocol.flag7", "Flag 7")
local flag_8 = ProtoField.bool("myprotocol.flag8", "Flag 8")

myprotocol.fields = { sequence_number, acknowledgement, flags, window, checksum, data, 
    flag_1, flag_2, flag_3, flag_4, flag_5, flag_6, flag_7, flag_8
}

function myprotocol.dissector(buffer, pinfo, tree)
    local offset = 0
    pinfo.cols.protocol = "MyProtocol"
    local subtree = tree:add(myprotocol, buffer(), "My Application Transmission Data Protocol")

    subtree:add(sequence_number, buffer(offset, 4))
    offset = offset + 4
    subtree:add(acknowledgement, buffer(offset, 4))
    offset = offset + 4

    local flag_val = buffer(offset, 1):uint()
    local flags_tree = subtree:add(flags, buffer(offset, 1), flag_val)

    local flags_field = {
        {mask = 0x01, field = flag_1, pattern = "*... ....", desc = "MES (Message)"},
        {mask = 0x02, field = flag_2, pattern = ".*.. ....", desc = "FIL (File)"},
        {mask = 0x04, field = flag_3, pattern = "..*. ....", desc = "KPL (Keep-alive)"},
        {mask = 0x08, field = flag_4, pattern = "...* ....", desc = "ACK (Acknowledgement)"},
        {mask = 0x10, field = flag_5, pattern = ".... *...", desc = "FF (FIRST_Fragment)"},
        {mask = 0x20, field = flag_6, pattern = ".... .*..", desc = "LF (Last_Fragment)"},
        {mask = 0x40, field = flag_7, pattern = ".... ..*.", desc = "SYN (Synchronize)"},
        {mask = 0x80, field = flag_8, pattern = ".... ...*", desc = "FIN (Finish)"}
    }

    for _, flag in ipairs(flags_field) do
        local set = bit.band(flag_val, flag.mask) ~= 0
        local set_or_not = flag.pattern:gsub("*", set and "1" or "0")
        local text = string.format("%s = %s: %s", set_or_not, flag.desc, set and "Set" or "Not set")
        flags_tree:add(flag.field, buffer(offset, 1), set):set_text(text)
    end
    
    offset = offset + 1
    subtree:add(window, buffer(offset, 2))
    offset = offset + 2
    subtree:add(checksum, buffer(offset, 2))
    offset = offset + 2

    if buffer:len() > offset then  -- if length equals 0 -> don't show data field
        local data_item = subtree:add(data, buffer(offset))
        data_item:set_text(string.format("Data: %d bytes", buffer:len() - offset))
    end
end

local myprotocolfind = DissectorTable.get("udp.port")
myprotocolfind:add(55002, myprotocol)