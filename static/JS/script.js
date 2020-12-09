function toggle() {
    let x = document.querySelectorAll("form");

    for (i = 0; i < x.length; i++) {
        if (x[i].classList.contains("invisible")) {
            x[i].classList.remove("invisible");
            x[i].classList.add("visible");
        } else {
            x[i].classList.remove("visible");
            x[i].classList.add("invisible");
        }
    }
}

function loginError() {
    let x = document.querySelector(".error-message");
        x.style.display = "block";
}
