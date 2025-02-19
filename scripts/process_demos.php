<?php
include('../config/db.php');
$db = get_db_connection();

$demo_file = 'path/to/demo.dem';
// Extract stats from demo file and update database
// Example:
$db->exec("INSERT INTO demos (player_id, demo_file) VALUES (1, '$demo_file')");
?>