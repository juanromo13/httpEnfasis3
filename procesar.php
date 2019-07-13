<?php
// Incluimos los datos de conexión y las funciones:
// Usamos esas variables:
  include("conexion.php");

  if(isset($_POST["src"], $_POST["dst"], $_POST["in"], $_POST["out"]) and $_POST["src"] !="" and $_POST["dst"]!="" and $_POST["in"]!="" and $_POST["out"]!=""){

    //traspasamos a variables locales, para evitar complicaciones con las comillas:
    $mac_src = $_POST['src'];
    $mac_dst = $_POST['dst'];
    $hora_in = $_POST['in'];
    $hora_out = $_POST['out'];

    //Preparamos la orden SQL
    $consulta = "INSERT INTO reglas(mac_src, mac_dst, hora_in, hora_out) VALUES ('$mac_src', '$mac_dst', '$hora_in', '$hora_out');";
    $result = mysqli_query($con,$consulta);

    if($result){
      echo "<p>Registro agregado.</p>";
    } else {
      echo "<p>No se agregó...</p>";
    }

  } else {

  echo '<p>Por favor, complete el <a href="index.html">formulario</a></p>';
  }

?>
