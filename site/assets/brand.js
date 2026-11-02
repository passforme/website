// The brand page: a colour swatch copies its code when clicked.
document.querySelectorAll(".swatch[data-copy]").forEach(function (b) {
  b.addEventListener("click", function () {
    var code = b.querySelector("code");
    var value = b.getAttribute("data-copy");
    navigator.clipboard.writeText(value).then(function () {
      b.classList.add("done");
      code.textContent = document.documentElement.lang.indexOf("pt") === 0 ? "copiado" : "copied";
      setTimeout(function () { b.classList.remove("done"); code.textContent = value; }, 1400);
    });
  });
});
