set sql to "sqlite3 '/Volumes/nour/synch.db' 'select iid, PCount from local where PCount != ipc'"
set a to do shell script sql 
set sql to "sqlite3 '/Volumes/nour/synch.db' 'update iUp SET UP = 1'"
set AppleScript's text item delimiters to {return}
set a to a's text items
set AppleScript's text item delimiters to {""} --> restore delimiters to default value
set AppleScript's text item delimiters to {"|"}
set b to {}
repeat with theItem in a
        set b to b & {theItem's text items}
end repeat
set AppleScript's text item delimiters to {""} --> restore delimiters to default value
repeat with tI in b
        tell application "iTunes" to set (played count of every track whose persistent ID is (item 1 of tI)) to (item 2 of tI)
end repeat
set sql to "sqlite3 '/Volumes/nour/synch.db' 'select distinct Plist from playlist'"
set nN to do shell script sql
set sql to "sqlite3 '/Volumes/nour/synch.db' 'select p.Plist, l.iid from playlist p, local l where l.ID = p.ID'"
set a to do shell script sql
set AppleScript's text item delimiters to {return}
set a to a's text items
set nN to nN's text items
set AppleScript's text item delimiters to {""} --> restore delimiters to default value
set AppleScript's text item delimiters to {"|"}
set b to {}
repeat with theItem in a
        set b to b & {theItem's text items}
end repeat
tell application "iTunes"
        repeat with p in nN
                if name of every playlist does not contain p then
                        make new user playlist with properties {name:p}
                else
                        delete tracks of playlist p
                end if
        end repeat
        repeat with nT in b
                set nP to item 1 of nT
                set nS to (first track whose persistent ID is item 2 of nT)
                if (tracks of playlist nP is {}) or (name of some track in playlist nP does not contain name of nS) then
                        duplicate nS to playlist nP
                end if
        end repeat
end tell
