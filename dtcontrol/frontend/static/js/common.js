function openNav() {
    // if (isSimulator) return;
    document.getElementById("mySidenav").style.width = "310px";
    document.getElementById("main").style.paddingLeft = "310px";
}

/* Set the width of the side navigation to 0 and the left margin of the page content to 0 */
function closeNav() {
    // if (isSimulator) return;
    document.getElementById("mySidenav").style.width = "0";
    document.getElementById("main").style.paddingLeft = "0";
}

$(document).ready(function () {
    openNav();
    document.getElementById("navbar-hamburger").className += " is-active";
});