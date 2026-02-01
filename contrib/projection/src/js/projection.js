import { Session } from "./fan";
//import { Clappr } from "@clappr/player";
import Clappr from "clappr";

const token_input = document.querySelector("#token");

const token = window.localStorage.getItem("token");
if (token != null) {
  token_input.value = token;
}

async function connect(token) {
  const fan = new Session();
  fan.on_connect = async () => {
    await fan.request("authenticate", {
      room: "secret_room",
      token: token,
    });
    console.log("authenticated");
  };
  await fan.connect(`ws://${window.location.host}/rpc`);
  return fan;
}

let fan;
document.querySelector("#do_auth").onclick = async () => {
  document.querySelector("#error").textContent = "";
  try {
    fan = await connect(token_input.value);
    window.localStorage.setItem("token", token_input.value);
    display_player();
  } catch (error) {
    console.log("do_auth:", error);
    document.querySelector("#error").textContent = error.message;
  }
};

function display_player() {
  document.querySelector("#auth").style.display = "none";
  document.querySelector("#player").style.display = "block";
  var player = new Clappr.Player({
    source:
      "https://archive.org/download/BigBuckBunny_124/Content/big_buck_bunny_720p_surround.mp4",
    parentId: "#player",
    width: "100%",
    autoPlay: false,
  });
  console.log("player", player);
}
