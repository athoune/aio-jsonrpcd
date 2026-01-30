import { Fireworks } from "fireworks-js";

const container = document.querySelector(".fireworks");
const fireworks = new Fireworks.default(container, { explosion: 1 });
//fireworks.start();

const socket = new WebSocket(`ws://${window.location.host}/rpc`);
socket.addEventListener("error", (event) => {
  console.log("WebSocket error:", event);
});
socket.addEventListener("close", (event) => {
  console.log("Closed connection");
});
socket.addEventListener("open", (event) => {
  console.log("Connected");
});
socket.addEventListener("message", (event) => {
  console.log("receive:", event.data);
  const req = JSON.parse(event.data);
  console.log(req);
  if (req.method == "all.fireworks") {
    fireworks.start();
  }
});

function auth() {
  let state = "auth";

  document.querySelector("#fire").onclick = (event) => {
    console.log("Click");
    let message = null;
    if (state == "auth") {
      message = JSON.stringify({
        jsonrpc: "2.0",
        method: "authenticate",
        id: 1,
        params: {
          room: "secret_room",
          token: document.querySelector("#token").value,
        },
      });
      state = "fire";
      document.querySelector("#fire").firstChild.data = "Fire !";
    } else {
      message = JSON.stringify({
        jsonrpc: "2.0",
        method: "all.fireworks",
        params: ["red"],
      });
    }
    console.log("send:", message);
    socket.send(message);
  };
}

auth();
console.log("hop");
