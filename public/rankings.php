<?php
include('../config/db.php');
$db = get_db_connection();

$result = $db->query('SELECT * FROM players ORDER BY kd_ratio DESC');
while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
    echo "Name: " . $row['name'] . " - K/D Ratio: " . $row['kd_ratio'] . "<br>";
}
?>