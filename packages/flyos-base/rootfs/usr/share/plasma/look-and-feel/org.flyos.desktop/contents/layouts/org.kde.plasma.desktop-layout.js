// Fly OS 0.5 default Plasma canvas.
// Fly Shell provides the primary bar/dock/launcher. Plasma remains the
// desktop/session fallback and KWin remains the compositor.
var desktops = desktopsForActivity(currentActivity());
for (var i = 0; i < desktops.length; i++) {
    var desktop = desktops[i];
    desktop.wallpaperPlugin = "org.kde.image";
    desktop.currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
    desktop.writeConfig("Image", "file:///usr/share/wallpapers/FlyOS/contents/images/3840x2160.svg");
    desktop.writeConfig("FillMode", 2);
}

var oldPanels = panels();
for (var p = 0; p < oldPanels.length; p++) {
    oldPanels[p].remove();
}
