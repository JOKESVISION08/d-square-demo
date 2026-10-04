import { signInWithEmailAndPassword, signOut, onAuthStateChanged } from "firebase/auth";
import { auth, isConfigured } from "./config";

const LOCAL_USER_KEY = "dsquare_operator_user";

export function getStoredUser() {
  const storedUserJson = localStorage.getItem(LOCAL_USER_KEY);
  if (storedUserJson) {
    try {
      return JSON.parse(storedUserJson);
    } catch (e) {
      // ignore
    }
  }
  const defaultDemoUser = {
    uid: "OP_LOCAL_ADMIN_01",
    email: "operator@dsquare.gov.in",
    displayName: "Authorized Chief Operator",
    role: "OPERATOR"
  };
  localStorage.setItem(LOCAL_USER_KEY, JSON.stringify(defaultDemoUser));
  return defaultDemoUser;
}

export function subscribeToAuth(callback) {
  // Always emit initial stored / default demo user immediately
  const initialUser = getStoredUser();
  callback(initialUser);

  if (!isConfigured) {
    return () => {};
  }

  return onAuthStateChanged(auth, (user) => {
    if (user) {
      const userObj = {
        uid: user.uid,
        email: user.email,
        displayName: user.displayName || user.email.split("@")[0],
        role: user.email.includes("rescue") ? "RESCUER" : "OPERATOR"
      };
      localStorage.setItem(LOCAL_USER_KEY, JSON.stringify(userObj));
      callback(userObj);
    }
  });
}

export async function loginUser(email, password) {
  const demoUser = {
    uid: "OP_LOCAL_ADMIN_01",
    email: email || "operator@dsquare.gov.in",
    displayName: "Authorized Chief Operator",
    role: "OPERATOR"
  };

  try {
    if (isConfigured) {
      const credential = await signInWithEmailAndPassword(auth, email, password);
      const user = credential.user;
      const userObj = {
        uid: user.uid,
        email: user.email,
        displayName: user.displayName || user.email.split("@")[0],
        role: user.email.includes("rescue") ? "RESCUER" : "OPERATOR"
      };
      localStorage.setItem(LOCAL_USER_KEY, JSON.stringify(userObj));
      return userObj;
    }
  } catch (err) {
    console.warn("Firebase auth login notice, using demo session:", err.message);
  }

  localStorage.setItem(LOCAL_USER_KEY, JSON.stringify(demoUser));
  return demoUser;
}

export async function logoutUser() {
  localStorage.removeItem(LOCAL_USER_KEY);
  if (isConfigured) {
    try {
      await signOut(auth);
    } catch (err) {
      // ignore
    }
  }
  return true;
}

