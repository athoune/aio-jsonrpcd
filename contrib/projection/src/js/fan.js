export class Session {
  constructor(on_event = null) {
    this.id = 0;
    this.responses = new Map();
    this.on_event = on_event;
    this.prehook = null;
  }

  async connect(url) {
    this.socket = new WebSocket(url);
    this.socket.addEventListener("message", (event) => {
      console.log("message", event, this);
      this._handle_message(event.data);
    });
    return new Promise((resolve, reject) => {
      try {
        const timeout = setTimeout(() => {
          this.socket.close();
          reject("Timeout");
        }, 3000);
        this.socket.addEventListener("open", (event) => {
          console.log("Connected");
          clearTimeout(timeout);
          resolve(event);
        });
        this.socket.addEventListener("error", (event) => {
          console.log("connect error:", event);
          clearTimeout(timeout);
          reject(event);
        });
      } catch (error) {
        console.log("connect caught error", error);
        clearTimeout(timeout);
        reject(error);
      }
    });
  }

  _handle_message(raw_message) {
    const message = JSON.parse(raw_message);
    if (message.error != null) {
      this.responses.get(message.id).reject(message);
    } else if (message.response != null) {
      this.responses.get(message.id).resolve(message);
      return;
    } else if (message.method != null) {
      if (message.id == null) {
        this.on_event(message);
      } else {
        // a call from the server
      }
    }
  }

  async request(method, params = null) {
    if (params == null) {
      params = {};
    }
    const id = this.id++;
    this.socket.send(
      JSON.stringify({
        jsonrpc: "2.0",
        id: id,
        method: method,
        params: params,
      }),
    );
    return new Promise((resolve, reject) => {
      try {
        console.log("request", this);
        this.responses.set(id, {
          reject: reject,
          resolve: resolve,
        });
      } catch (error) {
        reject(error);
      }
    });
  }
}
