const socket = io();
socket.on('connect', () => {
    console.log('connected11');
    socket.emit('my event', {data: 'I\'m connected!'});
});
socket.on('my response', data => {
    console.log('in my response', data);
});

function isOpen(target) {
    return target.classList.contains('open')
}
function closeVideo(target) {
    target.classList.remove('open');
}

function openVideo(target) {
    target.classList.add('open');
}

const videoElement = document.querySelector('.driver-block__camera');
videoElement.addEventListener('mousedown', e => {
    const video = e.target;
    const videoId = video.id;
    console.log(videoId);
    // console.log(video);
    // const video = videoElement;
    console.log(video);
    if (isOpen(video)) {
        closeVideo(video);
        console.log('video is closed');
    } else {
        socket.emit('ask video', {url: 'url', 'video_id': videoId});
        openVideo(video);
        console.log('video is opened');
    }
});
socket.on('response frame', frame => {
    console.log('display video: ', frame);
    // const videoElement = frame.video_element;
    const videoId = frame.video_id;
    const videoElement = document.getElementById(videoId);
    if (isOpen(videoElement)) {
        console.log('asking vide ...');
        socket.emit('ask video', {url: 'url', 'video_id': videoId});
    }
})