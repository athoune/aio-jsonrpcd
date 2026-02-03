export class Session {
  constructor(on_event = null) {
    this.id = 0;
    this.responses = new Map();
    this.on_event = on_event;
    this.on_connect = null;
    this.login = null;
  }

  async connect(url) {
    await this._connect(url);
    if (this.on_connect != null) {
      await this.on_connect();
    }
  }

  async _connect(url) {
    this.socket = new WebSocket(url);
    this.socket.addEventListener("message", (event) => {
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
    console.log("message:", message);
    if (message.error != null) {
      if (message.id != null) {
        this.responses.get(message.id).reject(message);
      } else {
        // it's an anonymous event error. Lets log it
        console.log(message);
      }
    } else if (message.result != null) {
      this.responses.get(message.id).resolve(message);
      return;
    } else if (message.method != null) {
      if (message.id == null) {
        if (this.on_event == null) {
          console.log("Event received:", message);
        } else {
          const handler = this.on_event[message.method];
          if (handler === undefined) {
            console.log("No event handler for ", message);
          } else {
            handler(message);
          }
        }
      } else {
        // a call from the server
      }
    }
  }

  event(method, params = null) {
    if (params == null) {
      params = {};
    }
    this.socket.send(
      JSON.stringify({
        jsonrpc: "2.0",
        method: method,
        params: params,
      }),
    );
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
