<?php
include('../config/db.php');
$db = get_db_connection();

$player_id = $_GET['id'];
$result = $db->query("SELECT * FROM players WHERE id = $player_id");
while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
    echo "Name: " . $row['name'] . " - Kills: " . $row['kills'] . "<br>";
}
?>