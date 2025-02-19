<?php
include('../config/db.php');
$db = get_db_connection();

$result = $db->query('SELECT * FROM players');
while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
    echo "Name: " . $row['name'] . " - Kills: " . $row['kills'] . "<br>";
}
?>