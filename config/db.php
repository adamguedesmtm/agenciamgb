<?php
function get_db_connection() {
    $db = new SQLite3('path/to/database.db');
    if (!$db) {
        echo $db->lastErrorMsg();
    }
    return $db;
}
?>