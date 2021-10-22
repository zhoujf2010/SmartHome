<template>
  <div class="ep-message-list">
    <MessageItem v-for="(messageItem, index) in list" :key="index" 
      :message="messageItem" 
      :entityTypes="entityTypes" 
      :max-rows="maxRows" 
      :intentionTypes="_getintentionTypes(messageItem.calltype)" 
      :editable="messageEditable" 
      :removable="messageRemovable" 
      :isFirst="index == 0" 
      :isLast="index == list.length - 1" 
      :typeList="messageTypeList"
      @remove-message="removeItem(index, messageItem)" 
      @move-up="move(index, -1)" 
      @move-down="move(index, 0)" 
      @clear-entity="clearEntity(messageItem)" 
      @on-edit="handleMessageEdit(messageItem, index)" 
      @on-refresh="handleMessageRefresh(messageItem, index)"
      @on-label-change="handleIntentionChange($event, messageItem, index)"
      @on-hatlabel-change="handleHatLabelChange($event, messageItem, index)"
    ></MessageItem>
  </div>
</template>

<style lang="scss">
.ep-message-list {
  position: relative;
  padding: 4px;
}
</style>

<script>
import MessageItem from "./components/MessageItem";

export default {
  name: "message-list",
  components: {
    MessageItem
  },
  data() {
    return {
      list: [],
      entityTypes: [],
      intentionTypes: {},
      // 消息是否可编辑
      messageEditable: true,
      // 消息是否可删除
      messageRemovable: true,
      // 已经删除的消息的集合
      removedItems: [],
      maxRows: 5,
      // 消息类型的列表
      messageTypeList: []
    };
  },
  methods: {
    getMaxRows() {
      return this.maxRows;
    },
    setMaxRows(v) {
      this.maxRows = parseInt(v, 10) || 5;
    },
    simplyCopy(data) {
      return JSON.parse(JSON.stringify(data));
    },
    setData(data) {
      this.setMessageList(data.messages || []);
      this.setEntityList(data.entityTypes || []);
      this.setIntentList(data.intentions || {});
      this.setMessageTypeList(data.messageTypeList || []);
    },
    setMessageList(messages) {
      this.clearRemoveItems();
      messages.forEach(item => {
        if (item.checked === undefined) {
          item.checked = false;
        }
        if (!item.entities) {
          item.entities = [];
        } else {
          item.entities.forEach(ent => {
            if (!ent.length) {
              ent.length = ent.value.length;
            }
            if (!ent.end) {
              ent.end = ent.start + ent.length;
            }
          });
        }
        if (!item.labeltype) {
          item.labeltype = '';
        }
        if (!item.labeltype_hat) {
          item.labeltype_hat = '';
        }
      });
      this.$set(this, "list", messages);
    },
    getSelecteds(key) {
      const selecteds = this.getMessageList().filter(item => item.checked);
      if (key === undefined) {
        return selecteds;
      }
      return selecteds.map(item => item[key]);
    },
    setEntityList(entityTypes) {
      this.$set(this, "entityTypes", entityTypes);
    },
    setIntentList(intentions) {
      this.$set(this, "intentionTypes", intentions);
    },
    getMessageList() {
      return this.simplyCopy(this.list);
    },
    setMessageEditable(v) {
      this.messageEditable = !!v;
    },
    removeItem(index, item) {
      this.removedItems.push(this.simplyCopy(item));
      this.list.splice(index, 1);
    },
    clearRemoveItems() {
      this.$set(this, "removedItems", []);
    },
    getRemoveItems(key) {
      if (key === undefined) {
        return this.simplyCopy(this.removedItems);
      }
      const arr = [];
      this.removedItems.forEach(item => {
        arr.push(item[key]);
      });
      return arr;
    },
    clearEntity(item) {
      item.entities.splice(0, item.entities.length);
    },
    _getintentionTypes(type) {
      return this.intentionTypes[type] || [];
    },
    /**
     * 交换排序移动
     * @param {Number} index 待排序元素索引
     * @param {enum} direction 移动方向 上移为-1 下移0；
     */
    move(index, direction) {
      const startIdx = index + direction;
      const its = this.list.slice(startIdx, startIdx + 2);
      if (its.length < 2) {
        return;
      }
      this.list.splice(startIdx, 2, its[1], its[0]);
    },
    handleMessageEdit(msg, index) {
      var prevItem = this.list[index - 1];
      if (typeof this.onMessageEdit == "function") {
        this.onMessageEdit(msg, prevItem);
      }
    },
    handleMessageRefresh(msg, index) {
      var prevItem = this.list[index - 1];
      if (typeof this.onMessageRefresh == "function") {
        this.onMessageRefresh(
          msg,
          prevItem,
          this.updateMesage.bind(this, index)
        );
      }
    },
    handleLabelChange(currentLabelId, message, index) {
      if (typeof this.onMessageLabelChange == "function") {
        this.onMessageLabelChange(currentLabelId, message, index);
      }
    },
    handleHatLabelChange(currentLabelId, message, index) {
      if (typeof this.onMessageHatLabelChange == "function") {
        this.onMessageHatLabelChange(currentLabelId, message, index);
      }
    },
    /* eslint no-unused-vars:0 */
    onMessageRefresh(item, prevQ) {},
    onMessageEdit(item, prevQ, update) {},
    updateMesage(index, newMsg) {
      this.list.splice(index, 1, newMsg);
    },
    onMessageIntentionChange(currentIntention, message, index) {},
    setMessageTypeList(list) {
      this.messageTypeList = list;
    },
    getMessageTypeList(list) {
      return this.messageTypeList;
    }
  }
};
</script>
