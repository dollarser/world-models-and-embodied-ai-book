window.MathJax = {
  tex: {
    // 全书使用 $…$ / $$…$$ 定界符（arithmatex generic 模式保留原样包裹）。
    inlineMath: [["$", "$"], ["\\(", "\\)"]],
    displayMath: [["$$", "$$"], ["\\[", "\\]"]],
    processEscapes: true
  },
  options: {
    processHtmlClass: "arithmatex"
  }
};

// MathJax 启动时会自动 typeset 静态页面；此处仅在库加载成功后补一次幂等 typeset，
// 不依赖任何 UMD 内部全局（浏览器构建不暴露 document$）。
(function () {
  function retypeset() {
    if (window.MathJax && typeof window.MathJax.typesetPromise === "function") {
      window.MathJax.typesetPromise().catch(function (err) {
        console.warn("MathJax retypeset failed:", err);
      });
    }
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      setTimeout(retypeset, 0);
    });
  } else {
    setTimeout(retypeset, 0);
  }
})();
