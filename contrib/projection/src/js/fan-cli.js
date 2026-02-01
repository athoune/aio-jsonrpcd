import { Session } from "./fan.js";

const fan = new Session();
await fan.connect("ws://localhost:8080/rpc");
const ping = await fan.request("ping");
console.log(ping);
