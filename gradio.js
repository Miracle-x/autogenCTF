//encoding=utf-8

var containers = document.querySelectorAll('.container');


function scrollToBottom(container) {
    container.scrollTop = container.scrollHeight;
}


var observer = new MutationObserver(function (mutationsList) {
    mutationsList.forEach(function (mutation) {
        if (mutation.type === 'childList') {
            scrollToBottom(mutation.target.parentElement);
        }
    });
});


containers.forEach(function (container) {
    observer.observe(container.querySelector('.content'), {childList: true});
});