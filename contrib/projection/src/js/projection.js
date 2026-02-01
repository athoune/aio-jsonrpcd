import { Clappr } from "@clappr/player";
import { Session } from "./fan";

const token_input = document.querySelector("#token");

const token = window.localStorage.getItem("token");
if (token != null) {
  token_input.value = token;
}

document.querySelector("#do_auth").onclick = async () => {
  console.log("click", token_input.value);
  document.querySelector("#error").textContent = "";
  try {
    const msg = await authenticate(token_input.value);
    console.log("authenticated", msg);
    window.localStorage.setItem("token", token_input.value);
    display_player();
  } catch (error) {
    document.querySelector("#error").textContent = error.error.message;
  }
};

let fan;
async function _connect() {
  if (fan == null) {
    // lazy connection
    fan = new Session();
    await fan.connect(`ws://${window.location.host}/rpc`);
  }
}

async function authenticate(token) {
  await _connect();
  return fan.request("authenticate", {
    room: "secret_room",
    token: token,
  });
}

function display_player() {
  document.querySelector("#player").style.display = "default";
  document.querySelector("#auth").style.display = "none";
  var player = new Clappr.Player({
    source:
      "https://archive.org/download/BigBuckBunny_124/Content/big_buck_bunny_720p_surround.mp4",
    parentId: "#player",
  });
  console.log("player", player);
}
