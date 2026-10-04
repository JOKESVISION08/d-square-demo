import '@testing-library/jest-dom';

// Mock Web Audio API and HTMLMediaElement for tests
class MockAudioContext {
  constructor() {
    this.state = 'suspended';
  }
  resume() {
    this.state = 'running';
    return Promise.resolve();
  }
  createOscillator() {
    return {
      type: 'sine',
      frequency: {
        setValueAtTime: () => {},
        exponentialRampToValueAtTime: () => {}
      },
      connect: () => {},
      start: () => {},
      stop: () => {}
    };
  }
  createGain() {
    return {
      gain: {
        setValueAtTime: () => {},
        exponentialRampToValueAtTime: () => {}
      },
      connect: () => {}
    };
  }
  get destination() {
    return {};
  }
  get currentTime() {
    return 0;
  }
}

global.AudioContext = global.AudioContext || MockAudioContext;
global.webkitAudioContext = global.webkitAudioContext || MockAudioContext;

// Mock HTMLMediaElement play & pause for jsdom
window.HTMLMediaElement.prototype.play = function() {
  return Promise.resolve();
};
window.HTMLMediaElement.prototype.pause = function() {};
window.HTMLMediaElement.prototype.load = function() {};
