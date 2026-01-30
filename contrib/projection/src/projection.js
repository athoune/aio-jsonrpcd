import { Clappr } from "@clappr/player";
import { connect } from "./fan";

async function popo() {
  const fan = await connect(`ws://${window.location.host}/rpc`);
  try {
    let response = await fan.request("authenticate", {
      room: "secret_room",
      token:
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2dpbiI6ImFsaWNlIiwicm9vbSI6InNlY3JldF9yb29tIn0.fyxF81FOR5I2tPJwRHyq9B6ftRsZo2bJ2ZIYtL7RjTY",
    });
    console.log(response);
  } catch (error) {
    console.log(error);
  }
}

popo();
