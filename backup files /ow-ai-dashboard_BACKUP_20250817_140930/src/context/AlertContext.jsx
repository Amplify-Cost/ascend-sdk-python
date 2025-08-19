import React, { createContext, useState, useContext } from "react";

const AlertContext = createContext();

export const useAlert = () => useContext(AlertContext);

export const AlertProvider = ({ children }) => {
  const [toastAlert, setToastAlert] = useState(null);
  const [bannerAlert, setBannerAlert] = useState(null);

  const showAlert = (message, data = {}) => {
    setToastAlert({ message, ...data });
    setBannerAlert({ message, ...data });

    setTimeout(() => setToastAlert(null), 5000); // Toast auto-dismiss
  };

  const dismissBanner = () => setBannerAlert(null);

  return (
    <AlertContext.Provider
      value={{ toastAlert, bannerAlert, showAlert, dismissBanner }}
    >
      {children}
    </AlertContext.Provider>
  );
};
