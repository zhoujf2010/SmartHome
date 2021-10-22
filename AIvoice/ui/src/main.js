import Vue from 'vue';
import MessageList from './MessageList.vue';

Vue.config.productionTip = false;


import './plugins/element.js';
mockData.messages.forEach(item => {
  if (!item.entities) {
    item.entities = [];
  }
});

const app = new Vue({
  render: h => h(MessageList)
}).$mount('#app');
var MessageEntityList = app.$children[0];
window.MessageEntityList = MessageEntityList;
MessageEntityList.setMessageEditable(true);
MessageEntityList.setData(window.mockData);
