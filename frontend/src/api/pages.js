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
};

export const blocksApi = {
  create(blockData) {
    return apiClient.post("/blocks/", blockData);
  },

  update(uid, blockData) {
    return apiClient.patch(`/blocks/${uid}/`, blockData);
  },

  delete(uid) {
    return apiClient.delete(`/blocks/${uid}/`);
  },
};
