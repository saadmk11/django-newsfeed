window.addEventListener("load", function () {
  let form = document.getElementById("subscriptionForm");
  let messageElement = document.getElementById("subscriptionMessage");

  form.addEventListener("submit", async function (event) {
    event.preventDefault();
    const data = new FormData(form);

    fetch(form.dataset.url, {
      method: "post",
      body: data,
      credentials: "include",
    })
      .then(function (response) {
        response.json().then(function (data) {
          if (response.status !== 200) {
            error_message = data.email_address;
            messageElement.innerText = error_message;
            messageElement.classList.remove("success");
            messageElement.classList.add("error");
          } else {
            messageElement.innerText = data.message;
            form.reset();

            if (data.success) {
              messageElement.classList.remove("error");
              messageElement.classList.add("success");
            } else {
              messageElement.classList.remove("success");
              messageElement.classList.add("error");
            }
          }
        });
      })
      .catch(function (error) {
        console.log(error);
        messageElement.innerText = "An error occurred, please try again";
        messageElement.classList.remove("success");
        messageElement.classList.add("error");
      });
  });
});
