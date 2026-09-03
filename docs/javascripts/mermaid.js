// 渲染书中全部 mermaid 图（`mermaid-src` 围栏）并居中。
// 主题自带加载器从 unpkg 动态拉取 mermaid，部分网络不可达；
// 这里固定从 jsDelivr 加载同版本构建，保证渲染可用。
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
  var s = document.createElement("script");
  s.src = "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js";
  s.onload = boot;
  document.head.appendChild(s);
})();
