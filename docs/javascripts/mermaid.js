// 渲染书中全部 mermaid 图（`mermaid-src` 围栏）并居中。
// mermaid 构建自托管在 /javascripts/mermaid.min.js（与本页同源，
// 不依赖任何第三方 CDN，保证在受限网络下也能渲染）。
(function () {
  function boot() {
    var nodes = Array.prototype.slice.call(document.querySelectorAll("pre.mermaid-src"));
    if (!nodes.length) return;
    if (!window.mermaid) return;
    mermaid.initialize({ startOnLoad: false });
    nodes.forEach(function (node, i) {
      var codeEl = node.querySelector("code");
      var text = (codeEl ? codeEl.textContent : node.textContent).replace(/^\n+|\n+$/g, "");
      mermaid
        .render("mermaid-render-" + i, text)
        .then(function (result) {
          var holder = document.createElement("div");
          holder.className = "mermaid-holder";
          holder.innerHTML = result.svg;
          node.parentNode.replaceChild(holder, node);
        })
        .catch(function (err) {
          console.error("Mermaid render failed:", err);
        });
    });
  }
  if (window.mermaid) {
    boot();
    return;
  }
  // 兼容 mermaid.min.js 尚未加载的加载顺序
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    setTimeout(boot, 0);
  }
})();
