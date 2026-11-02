// Each page exists once per language: English at the root, Portuguese
// under pt-br/, written by tools/pages.py from the sources in src/. The
// switch in the top bar links to the page's twin and the choice made
// there is remembered, for every page. Without a choice, the browser's
// language decides only on an English page, the default: a "pt" browser
// is sent to the Portuguese twin. A Portuguese URL never redirects by
// browser language, so a crawler (which reports en-US and runs scripts)
// sees it as it is, with its own canonical.
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
  var want = null;
  if (saved === "pt" || saved === "en") {
    want = saved;
  } else if (here === "en" && (navigator.language || "").toLowerCase().indexOf("pt") === 0) {
    want = "pt";
  }
  if (want && want !== here && twins[want]) location.replace(twins[want].href + location.hash);
})();
