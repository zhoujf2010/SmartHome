<template>
  <div class="ep-message-item" :class="{ expanded: expand, checked: message.checked }">
    <div class="ep-message-item-base">
      <el-checkbox v-model="message.checked" style="margin-right:10px" />
      <span class="ep-message-item-type">{{ message.calltype }}</span>
      <span class="ep-message-item-icon" :class="{ 'el-icon-plus': !expand, 'el-icon-minus': !!expand, unmarkable: !markable }" @click="handleToogle"></span>
      <el-select class="ep-message-item-select" v-model="message.labeltype" placeholder="请选择类型" @change="handleLabelChange">
        <el-option v-for="item in typeList" :key="item.id" :label="item.text" :value="item.id"></el-option>
      </el-select>
      <div class="ep-message-item-content" :class="{ removable: removable, showExtBtn: !markable }" @change="handleHatLabelChange">
        <TextBackdrop ref="textBackdrop" :editable="editable" v-model="message.message" :entities="message.entities" :entity-types="entityTypes" :max-rows="maxRows" @change="handleInputChange" @focus="remindOldValue" />
        <div class="ep-message-item-actions">
          <el-select class="ep-message-hattype-select" v-model="message.labeltype_hat" placeholder="请选择类型">
            <el-option v-for="item in typeList" :key="item.id" :label="item.text" :value="item.id"> </el-option>
          </el-select>
          <el-button class="ep-message-item-edit" plain icon="el-icon-edit" title="编辑" @click="handleMessageEdit" size="mini" v-if="!markable"></el-button>
          <el-button class="ep-message-item-refresh" plain icon="el-icon-refresh" title="刷新" @click="handleMessageRefresh" size="mini" v-if="!markable"></el-button>
          <el-button class="ep-message-item-up" plain icon="el-icon-arrow-up" title="上移" @click="handleUp" :disabled="isFirst"></el-button>
          <el-button class="ep-message-item-down" plain icon="el-icon-arrow-down" title="下移" @click="handleDown" :disabled="isLast"></el-button>
          <el-button class="ep-message-item-remove" plain icon="el-icon-delete" title="删除" @click="handleRemove" v-if="removable"></el-button>
        </div>
      </div>
    </div>
    <!-- 下拉展开 -->
    <div class="ep-message-item-spread" v-show="expand">
      <EntityList :list="message.entities" :typeList="entityTypes"></EntityList>
      <!-- <span v-if="currSelectedText" @click="handleAddEntity">
                为<span style="color:#f00;margin:0 2px;">{{currSelectedText}}</span>添加标记
            </span>
            <span v-else>选中文本来添加实体标记</span>-->
      <el-button type="primary" v-show="!!currSelectedText" @click="handleAddEntity" round
        >为 “<span class="ep-message-item-selected-text">{{ currSelectedText }}</span
        >” 添加标记</el-button
      >
      <el-button v-show="!currSelectedText" round plain disabled>选中文本来添加实体标记</el-button>
    </div>
  </div>
</template>

<script>
import { Button, Select, Option, Input, Checkbox } from 'element-ui';
import EntityList from './EntityList';
import TextBackdrop from './TextBackdrop';
export default {
  name: 'message-item',
  components: {
    EntityList,
    TextBackdrop,
    'el-button': Button,
    'el-select': Select,
    'el-option': Option,
    // "el-input": Input,
    'el-checkbox': Checkbox
  },
  data() {
    return {
      currSelectedStart: -1,
      currSelectedEnd: -1,
      currSelectedText: '',
      expand: false,
      // markable: false
      markable: this.message.calltype != 'A',
      oldValue: this.message.message || ''
    };
  },
  props: {
    maxRows: {
      type: Number
    },
    message: {
      type: Object,
      default: () => {
        return {};
      }
    },
    entityTypes: {
      type: Array,
      default: () => []
    },
    intentionTypes: {
      type: Array,
      default: () => []
    },
    typeList: {
      type: Array,
      default: () => []
    },
    editable: {
      type: Boolean,
      default: true
    },
    removable: {
      type: Boolean,
      default: true
    },
    isFirst: {
      type: Boolean,
      default: false
    },
    isLast: {
      type: Boolean,
      default: false
    }
  },
  watch: {
    'message.calltype': function(v) {
      this.markable = v != 'A';
    }
  },
  mounted() {
    this.$nextTick(() => {
      this.$refs.textBackdrop.$refs.elInput.$el.onselect = this.handleSelectedChange.bind(this);
    });
  },
  methods: {
    handleSelectedChange(ev) {
      var el = ev.target;
      this.currSelectedStart = el.selectionStart;
      this.currSelectedEnd = el.selectionEnd;
      this.currSelectedText = el.value.substring(this.currSelectedStart, this.currSelectedEnd);
    },
    resetCurrSelected() {
      this.currSelectedStart = -1;
      this.currSelectedEnd = -1;
      this.currSelectedText = '';
    },
    handleToogle() {
      this.expand = !this.expand;
      if (!this.expand) {
        this.resetCurrSelected();
      }
    },
    handleAddEntity() {
      if (!this.markable) {
        return;
      }
      const newEntity = {
        start: this.currSelectedStart,
        end: this.currSelectedEnd,
        value: this.currSelectedText,
        length: this.currSelectedText.length,
        entity: this.entityTypes[0].id
      };

      this.message.entities.push(newEntity);
    },
    handleRemove() {
      this.$emit('remove-message');
    },
    handleInputChange(v) {
      if (v.indexOf(this.oldValue) === -1) {
        this.$emit('clear-entity');
      }
      this.oldValue = v;
    },
    remindOldValue(ev) {
      this.oldValue = ev.target.value;
    },
    handleUp() {
      this.$emit('move-up');
    },
    handleDown() {
      this.$emit('move-down');
    },
    handleMessageEdit() {
      this.$emit('on-edit');
    },
    handleMessageRefresh() {
      this.$emit('on-refresh');
    },
    handleLabelChange() {
      this.$emit('on-label-change', this.message.intent);
    },
    handleHatLabelChange() {
      this.$emit('on-hatlabel-change', this.message.intent);
    }
  }
};
</script>

<style lang="scss">
$height: 28px;
$hoverBg: #fafafa;
.ep-message-hattype-select {
  width: 180px;
  margin-right: 10px;
}
.ep-message-item {
  position: relative;
  margin-bottom: 10px;
  &-base {
    // height: 40px;
    line-height: $height;
    padding: 6px 10px;
    box-sizing: border-box;
    display: flex;
    &:hover {
      background: $hoverBg;
    }
  }
  &-type,
  &-icon {
    // display: inline-block;
    text-align: center;
    border: 1px solid #ddd;
    width: $height;
    height: $height;
    line-height: $height;
    box-sizing: border-box;
    border-radius: 4px;
    vertical-align: top;
    margin-right: 10px;
    cursor: pointer;
    user-select: none;
  }
  &-icon.unmarkable {
    visibility: hidden;
  }
  &-select {
    width: 120px;
    height: $height;
  }
  &-content {
    position: relative;
    display: flex;
    flex-wrap: nowrap;
    justify-content: space-between;
    flex-grow: 1;
    // position: absolute;
    // height: $height;
    box-sizing: border-box;
    margin-left: 10px;
    // top: 6px;
    // right: 0;
    // left: $height * 2 + 120px + 50px + 24px;

    &:hover {
      .ep-message-item-edit,
      .ep-message-item-refresh,
      .ep-message-item-up,
      .ep-message-item-down {
        // visibility: visible;
        display: inline-block;
      }
      .ep-message-item-actions {
        width: 290px;
      }
    }
    &.showExtBtn:hover {
      .ep-message-item-actions {
        width: 370px;
      }
    }
    &.removable {
      .ep-message-item-actions {
        width: 266px;
      }
      .ep-message-item-remove {
        display: inline-block;
      }
      &:hover .ep-message-item-actions {
        width: 350px;
      }
      &.showExtBtn:hover .ep-message-item-actions {
        width: 434px;
      }
    }
  }

  &-actions {
    width: 200px;
    text-align: right;
  }
  &-edit,
  &-refresh,
  &-up,
  &-down,
  &-remove {
    height: $height;
    line-height: $height - 2px;
    vertical-align: top;

    padding-top: 0;
    padding-bottom: 0;
    height: $height;
    line-height: $height - 2px;
    vertical-align: top;
  }
  &-edit,
  &-refresh,
  &-up,
  &-down {
    padding-left: 8px;
    padding-right: 8px;
    display: none;
    // visibility: hidden;
    // opacity: 0;
    // transition: all .1s .1s ease-out;
  }
  &-remove {
    display: none;
    // position: absolute;
    // // right: 0;
    // padding-top: 0;
    // padding-bottom: 0;
    // height: $height;
    // line-height: $height - 2px;
    // vertical-align: top;
  }
  &-spread {
    padding: 10px;
    padding-left: $height * 2 + 30px + 24px;
    overflow: hidden;
    &:hover {
      background: $hoverBg;
    }
  }
  &-selected-text {
    margin: 0 2px;
    max-width: 400px;
    display: inline-block;
    text-overflow: ellipsis;
    overflow: hidden;
    white-space: nowrap;
    vertical-align: bottom;
  }

  .el-input__inner {
    vertical-align: top;
    height: $height;
    line-height: $height - 2px;
  }
  .el-input__icon {
    line-height: $height - 2px;
  }
}
</style>
