/**
 * @file env.js
 * @description This module exports environment variables used in the application.
 */

const BASE_API = import.meta.env.VITE_API_BASE_URL;
if (!BASE_API) {
    console.error("Environment variable VITE_API_BASE_URL is not defined.");
}

const HOME_URL = import.meta.env.VITE_BACKEND_URL;
if (!HOME_URL) {
    console.error("Environment variable VITE_BACKEND_URL is not defined.");
}

const LOGIN_URL = import.meta.env.VITE_LOGIN_URL;
if (!LOGIN_URL) {
    console.error("Environment variable VITE_LOGIN_URL is not defined.");
}

const DEBUG = import.meta.env.VITE_DEBUG === 'true';

export { BASE_API, HOME_URL, LOGIN_URL, DEBUG };
