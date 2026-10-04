/**
 * Audio & Alert Sound Engine for D-SQUARE 2.0
 * Uses the sossound folder MP3 alert sound (/sossound/tithuh-warning-545568.mp3)
 * as the sole alert sound across D-SQUARE GPT, Rescue GPT, and all alert notifications.
 */

const SOS_AUDIO_PATH = '/sossound/tithuh-warning-545568.mp3';

let sosAudioElement = null;
let isMuted = false;
let continuousAlarmInterval = null;

function getSosAudioElement() {
  if (typeof window === 'undefined') return null;
  if (!sosAudioElement) {
    sosAudioElement = new Audio(SOS_AUDIO_PATH);
    sosAudioElement.preload = 'auto';
  }
  return sosAudioElement;
}

export function initAudioContext() {
  // Pre-load sossound audio element on user interaction
  try {
    const audioEl = getSosAudioElement();
    if (audioEl) {
      audioEl.load();
    }
  } catch (err) {
    console.warn("sossound audio pre-load notice:", err);
  }
}

export function setAudioMuted(muted) {
  isMuted = muted;
  if (isMuted && sosAudioElement) {
    try {
      sosAudioElement.pause();
    } catch (e) {
      // ignore
    }
  }
}

export function getAudioMuted() {
  return isMuted;
}

/**
 * Plays the sossound alert sound once for single notifications or dispatches.
 */
export function playSosAlarmSound() {
  if (isMuted) return;

  try {
    const audioEl = getSosAudioElement();
    if (audioEl) {
      audioEl.currentTime = 0;
      audioEl.loop = false;
      const promise = audioEl.play();
      if (promise !== undefined) {
        promise.catch(err => {
          console.warn("sossound audio playback notice:", err);
        });
      }
    }
  } catch (err) {
    console.warn("sossound alert sound error:", err);
  }
}

// Alias playDispatchBeep & playSosAlarmBeeps to play default sossound alert sound
export const playDispatchBeep = playSosAlarmSound;
export const playSosAlarmBeeps = playSosAlarmSound;

/**
 * Plays the sossound alert sound on a continuous loop for active SOS alerts in D-SQUARE GPT & Rescue GPT.
 */
export function startContinuousSosAlarm() {
  if (isMuted) return;

  try {
    const audioEl = getSosAudioElement();
    if (audioEl) {
      audioEl.currentTime = 0;
      audioEl.loop = true;
      const promise = audioEl.play();
      if (promise !== undefined) {
        promise.catch(err => {
          console.warn("sossound loop play notice (retrying via interval):", err);
          if (!continuousAlarmInterval) {
            continuousAlarmInterval = setInterval(() => {
              if (!isMuted) playSosAlarmSound();
            }, 2000);
          }
        });
      }
    }
  } catch (err) {
    console.warn("Continuous sossound alert error:", err);
  }
}

/**
 * Stops continuous sossound alert sound and resets playback.
 */
export function stopContinuousSosAlarm() {
  if (sosAudioElement) {
    try {
      sosAudioElement.pause();
      sosAudioElement.currentTime = 0;
    } catch (e) {
      // ignore
    }
  }
  if (continuousAlarmInterval) {
    clearInterval(continuousAlarmInterval);
    continuousAlarmInterval = null;
  }
}

export function isContinuousSosAlarmActive() {
  if (sosAudioElement && !sosAudioElement.paused) {
    return true;
  }
  return Boolean(continuousAlarmInterval);
}
