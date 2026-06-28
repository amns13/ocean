import apiClient from "./axios";

export const pagesApi = {
  getAll() {
    return apiClient.get("/pages/");
  },

  getOne(uid) {
    return apiClient.get(`/pages/${uid}/`);
  },

  create(pageData) {
    return apiClient.post("/pages/", pageData);
  },

  update(uid, pageData) {
    return apiClient.put(`/pages/${uid}/`, pageData);
  },

  delete(uid) {
    return apiClient.delete(`/pages/${uid}/`);
  },

  getPageBlocks(uid) {
    return apiClient.get(`/pages/${uid}/blocks/`);
  },
  uploadImage(uid, image) {
    const formData = new FormData();
    formData.append("image", image);
    return apiClient.post(`/pages/${uid}/upload-image/`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
};

export const blocksApi = {
  create(blockData) {
    return apiClient.post("/pages/blocks/", blockData);
  },

  update(uid, blockData) {
    return apiClient.patch(`/pages/blocks/${uid}/`, blockData);
  },

  delete(uid) {
    return apiClient.delete(`/pages/blocks/${uid}/`);
  },
};
