(function () {
  const DEMO_USER = "demo";
  const DEMO_PASS = "demo123";
  const SESSION_KEY = "portal_ponto_agil_logged";

  window.PortalAuth = {
    login: function (username, password) {
      if (username === DEMO_USER && password === DEMO_PASS) {
        sessionStorage.setItem(SESSION_KEY, "1");
        return true;
      }
      return false;
    },
    isLoggedIn: function () {
      return sessionStorage.getItem(SESSION_KEY) === "1";
    },
    requireAuth: function () {
      if (!this.isLoggedIn()) {
        window.location.href = "login.html";
        return false;
      }
      return true;
    },
    logout: function () {
      sessionStorage.removeItem(SESSION_KEY);
      window.location.href = "login.html";
    },
  };
})();
