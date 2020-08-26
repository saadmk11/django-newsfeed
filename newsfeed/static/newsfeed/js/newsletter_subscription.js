window.addEventListener("load", function () {
  let forms = document.querySelectorAll(".subscriptionForm");

  forms.forEach(function (form) {
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      let data = new FormData(form);
      let messageElement = form.querySelector(".subscriptionMessage");

      fetch(form.action, {
        method: "post",
        mode: "same-origin",
        body: data,
        credentials: "same-origin",
        headers: {
          Accept: "application/json",
          "X-Requested-With": "XMLHttpRequest",
        },
      })
      .then(function (response) {
        response.json().then(function (data) {
          if (response.status !== 200) {
            messageElement.innerText = data.email_address;
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
});
