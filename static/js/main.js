const socket = io();
socket.on('connect', () => {
  console.log('connected to server');
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

const videoElements = document.querySelectorAll('.driver-block__camera');
Array.from(videoElements).forEach(videoElement => {
  handle_video_clicks(videoElement);
});

function handle_video_clicks(videoElement) {
  videoElement.addEventListener('mousedown', e => {
    const video = e.target;
    const videoPath = video.id;
    const driver_folder = videoElement.closest('.driver-block').id;
  
    if (isOpen(video)) {
      closeVideo(video);
      socket.emit('stop video', 
        {'video_path': videoPath, 'driver_folder': driver_folder});
    } else {
      console.log('ask video ...');
      socket.emit('ask video', {'video_path': videoPath,
        'is_open': true, 'driver_folder': driver_folder});
      openVideo(video);
    }
  });
}

function putFrameInHtml(arrayBufferFrame, videoElement) {
  const blob = getBlobFromArrayBuffer(arrayBufferFrame);
  const reader = new FileReader();
  reader.onload = function () {
    const dataURL = reader.result;
    videoElement.src = dataURL;
  };
  reader.readAsDataURL(blob);
}

function getBlobFromArrayBuffer(frame) {
  const frameArray = new Uint8Array(frame);
  return new Blob([frameArray], { type: 'image/jpeg' });
}

const predicted_classes = [
  "нормальне водіння",
  "користування телефоном",
  "користування радіо",
  "Споживання напоїв",
  "Відволікання на речі позаду",
]
const NORMAL_DRIVING_CLASS = 0

function appendMessage(messagesElement, predictions_date, predictions) {
  const p = document.createElement('p');
  let stringMessage = `> ${predictions_date}: `;

  if (predictions[0].predicted_class === NORMAL_DRIVING_CLASS) {
    stringMessage += predicted_classes[NORMAL_DRIVING_CLASS];
    p.classList.add('normal');
  } else {
    stringMessage += createErrorMessage(predictions);
    p.classList.add('error');
  }
  p.innerText = stringMessage;
  messagesElement.append(p);
}

function createErrorMessage(predictions) {
  let message = `Відволікання: ймовірність ${predictions[0].probability}`
        + ` - ${predicted_classes[predictions[0].predicted_class]}`;
  if (predictions.length > 1) {
    message += `, ${predictions[1].probability} - ${predicted_classes[predictions[1].predicted_class]}`;
  }
  return message;
}

socket.on('response video', data => {
  console.log('display video: ', data);
  const videoElement = document.getElementById(data.video_path);

  putFrameInHtml(data.frame, videoElement);
  const parentDiv = videoElement.closest('.driver-block');
  const messagesElement = parentDiv.querySelector('.driver-block__messages');
  if (data.predictions) {
    appendMessage(messagesElement, data.predictions_date, data.predictions);
  }

})