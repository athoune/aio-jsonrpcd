export async function connect(url) {
  const c = new Connection(url);
  await c.connect();
  return c;
}

class Connection {
  constructor(url, on_event) {
    this.url = url;
    this.on_event = on_event;
    this.id = 0;
    this.responses = new Map();
  }

  async connect() {
    this.socket = new WebSocket(this.url);
    const _message = this._message;
    const conn = this;
    return new Promise((resolve, reject) => {
      this.socket.addEventListener("open", (event) => {
        console.log("Connected");
        resolve(event);
      });
      this.socket.addEventListener("error", (event) => {
        reject(event);
      });
      this.socket.addEventListener("message", (event) => {
        _message(conn, event);
      });
    });
  }

  async _message(conn, event) {
    // "this" is the websocket
    const message = JSON.parse(event.data);
    if (message.response != null) {
      const p = conn.responses[message.id];
      if (message.error != null) {
        p.reject(message);
      } else {
        p.resolve(message);
      }
      return;
    }
    if (message.method != null) {
      if (event.id == null) {
        conn.on_event(conn, event);
      } else {
        // a call from the server
      }
    } else {
      // it's a malformed message
    }
  }

  async request(method, params) {
    const id = this.id++;
    this.socket.send(
      JSON.stringify({
        jsonrpc: "2.0",
        id: id,
        method: method,
        params: params,
      }),
    );
    const responses = this.responses;
    return new Promise((resolve, reject) => {
      responses[id] = {
        reject: reject,
        resolve: resolve,
      };
    });
  }
}
