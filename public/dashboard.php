<?php
include('../config/db.php');
$db = get_db_connection();

$result = $db->query('SELECT * FROM active_servers');
while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
    echo "Server: " . $row['server_name'] . " - Status: " . $row['status'] . "<br>";
}
?>