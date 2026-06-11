## cURL

**`curl` is a command-line tool for transferring data from or to a server, using various protocols such as HTTP, HTTPS, FTP, and more.** It is widely used for making HTTP requests, including `GET`, `POST`, `PUT`, `DELETE`, and others.

Example of a `GET` request:

```bash
curl -X GET https://strathmore.edu/
```

or simply

```bash
curl https://strathmore.edu/
```

Where the default request method is `GET`.

This sends a `GET` request to the Strathmore University website. The response is displayed in the terminal, however, if the response was received by a browser, it would be rendered as a webpage because browsers can interpret the HTML, JavaScript, and CSS in the response.

`curl` can also be used to send HTTP POST requests to a server. The basic syntax for sending a POST request with `curl` is as follows:

```bash
curl -X POST <URL> \
  -H "Content-Type: <content-type>" \
  -d '<data>'
```

Where:
- `<URL>` is the **endpoint** to which you want to send the `POST` request.
- `<content-type>` is the type of data you are sending (e.g., `application/json` for JSON data).
- `<data>` is the actual data you want to send in the `POST` request. This can be a string, JSON, or any other format depending on the content type you specify. JSON is the most common format for sending data in a `POST` request.
- `-d` is the option to specify the data to be sent in the `POST` request.


The following is an example of a HTTP POST request to a free public echo server ([https://httpbin.org/](https://httpbin.org/)) through its `post` endpoint. It receives whatever you send and reflects it back in JSON.

```bash
curl -X POST https://httpbin.org/post \
  -H "Content-Type: application/json" \
  -d '{"name": "Musyoka", "course": "BBT 4106"}'
```

<img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/bash/bash-original.svg" width="200" alt="Bash Logo"/>

## Mapping it to the Bash Script in Part 3 of the Lab

The bash script contains the following line:

```bash
RESPONSE=$(render_template "$CONFIG_FILE" | curl -s -o /dev/null -w "%{http_code}" \
  -X POST "$CONNECT_URL" \
  -H "Content-Type: application/json" \
  -d @-)
```

This is interpreted as follows:

1. `render_template "$CONFIG_FILE"`: This command is executed first. It calls a function called `render_template` which generates the data that will be sent in the `POST` request. The output of this command is piped (`|`) to the `curl` command.
2. `-s -o /dev/null -w "%{http_code}"`: These options are used to suppress the output of the `curl` command and only return the HTTP status code of the response.
3. `-X POST "$CONNECT_URL"`: This specifies that the request method is `POST` and the URL to which the request is sent is stored in the variable `CONNECT_URL`.
4. `-H "Content-Type: application/json"`: This sets the `Content-Type` header to `application/json`, indicating that the data being sent is in JSON format.
5. `-d @-`: This tells `curl` to read the data from standard input (which is the output of the `render_template` command).
6. `RESPONSE` is the variable that will store the HTTP status code of the response.

### A Shell
A shell is **a command-line interpreter that provides a user interface for interacting with an Operating System.** Different shells offer different syntax, features, scripting capabilities, and user experiences.

There are different types of shells. For example:

- Bourne Shell (sh)
- Bourne Again Shell (Bash)
- C Shell (csh)
- Korn Shell (ksh)
- Z Shell (zsh)
- Fish Shell (fish)
- PowerShell

We use `Git Bash` in our labs which is a terminal that runs on Windows and allow us to access the Bourne Again Shell (Bash) shell.

### Difference between a Terminal and a Shell

- A terminal is a program that runs on your computer and allows you to interact with it via a command line interface (CLI).

- The shell is the program that interprets the commands you type in the terminal.

### Tutorials on Shell Scripting

**Shell scripting** is the process of writing shell scripts that can be executed by the shell. It allows you to automate tasks, manage system operations, and perform various functions on your computer.

It is an essential skill for system administrators.

The following site provides a tutorial on shell scripting: [https://www.tutorialspoint.com/unix/shell_scripting.htm](https://www.tutorialspoint.com/unix/shell_scripting.htm)

This lab uses the `Bourne Again Shell` (Bash) as indicated at the top of each Shell script (each `.sh` file): `#!/bin/bash`. You can read more about Bash scripting here: [https://www.gnu.org/software/bash/](https://www.gnu.org/software/bash/)