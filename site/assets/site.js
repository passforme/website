// Each page exists once per language: English at the root, Portuguese
// under pt/, written by tools/pages.py from the sources in src/. The switch
// in the top bar links to the page's twin. A choice made there is
// remembered; without one, the browser's language decides on the first
// page (Portuguese when it starts with "pt", English otherwise).
(function () {
  var here = document.documentElement.lang.slice(0, 2);
  var twins = {};
  document.querySelectorAll(".langs a[hreflang]").forEach(function (a) {
    var lang = a.getAttribute("hreflang").slice(0, 2);
    twins[lang] = a;
    a.addEventListener("click", function () {
      try { localStorage.setItem("pfm-lang", lang); } catch (e) {}
    });
  });
  var saved = null;
  try { saved = localStorage.getItem("pfm-lang"); } catch (e) {}
  var want = saved === "pt" || saved === "en" ? saved
    : (navigator.language || "en").toLowerCase().indexOf("pt") === 0 ? "pt" : "en";
  if (want !== here && twins[want]) location.replace(twins[want].href + location.hash);
})();
