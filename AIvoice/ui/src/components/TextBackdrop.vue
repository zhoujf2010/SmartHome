<template>
  <div class="ep-message-item-text" :style="styleObj">
    <el-input ref="elInput" class="ep-message-item-input" v-model="currentValue" :type="rows > 1 ? 'textarea' : 'text'" :rows="validateRows" :readonly="!editable" @change="handleInputChange" @focus="remindOldValue"></el-input>
    <!-- 文本选中背景 -->
    <Backdrop class="ep-message-item-backdrop" :messageText="value" :entities="entities" :entityTypes="entityTypes" :scroll-top="scrollTop"></Backdrop>
    <div class="ep-message-item-text-ghost" ref="ghost">{{ value || "&nbsp;"  }}</div>
  </div>
</template>

<script>
import { Input } from 'element-ui';
import Backdrop from './Backdrop';
/**
 * throttle 降低触发频率
 * 连续触发时，降低执行频率到指定时间
 *
 * @param {function} fn 要处理的函数
 * @param {number} delay 间隔时间 单位 ms
 * @param {[object]} ctx 要绑定的上下文
 * @returns throttle 后的新函数
 */
function throttle(fn, delay, ctx) {
  delay = delay || 200;
  var timer,
    prevTime = +new Date();
  return function() {
    clearTimeout(timer);
    var args = arguments;
    var context = ctx || this;
    var pastTime = +new Date() - prevTime;

    if (pastTime >= delay) {
      // 如果过去的时间已经大于间隔时间 则立即执行
      fn.apply(context, args);
      prevTime = +new Date();
    } else {
      // 过去的时间还没到 则等待
      timer = setTimeout(function() {
        fn.apply(context, args);
        prevTime = +new Date();
      }, delay - pastTime);
    }
  };
}

export default {
  name: 'TextBackdrop',
  components: { Backdrop, 'el-input': Input },
  props: {
    editable: Boolean,
    value: String,
    entities: Array,
    entityTypes: Array,
    maxRows: {
      type: Number,
      default: 5
    }
  },
  data() {
    return {
      currentValue: this.value,
      lineHeight: 26,
      rows: 1,
      scrollTop: 0,
      inputElement: null
    };
  },

  computed: {
    validateRows() {
      return this.rows <= this.maxRows ? this.rows : this.maxRows;
    },
    height() {
      return this.lineHeight * this.rows + 2;
    },
    styleObj() {
      return {
        height: this.height + 'px',
        lineHeight: this.lineHeight + 'px',
        maxHeight: this.lineHeight * this.maxRows + 2 + 'px'
      };
    }
  },
  methods: {
    calcHeight() {
      this.$nextTick(() => {
        const h = this.$refs.ghost.clientHeight;
        const rows = Math.ceil(h / this.lineHeight);
        this.rows = rows;
      });
    },
    handleInputChange(v) {
      this.$emit('input', v);
      this.$emit('change', v);
    },
    remindOldValue(ev) {
      this.$emit('focus', ev);
    },
    syncScroll() {
      this.$nextTick(() => {
        if (!this.inputElement) {
          return;
        }
        this.scrollTop = this.inputElement.scrollTop;
      });
    }
  },
  watch: {
    value() {
      this.currentValue = this.value;
      this.calcHeightThrottled();
    },
    maxRows() {
      this.calcHeight();
      this.syncScroll();
    }
  },
  created() {
    this.calcHeightThrottled = throttle(this.calcHeight, 50);
    this.syncScrollThrottled = throttle(this.syncScroll, 17);
  },
  mounted() {
    this.calcHeight();
    window.addEventListener('resize', this.calcHeightThrottled);
    this.$nextTick(() => {
      this.inputElement = this.$refs.elInput.$el.querySelector('.el-textarea__inner');
      if (this.inputElement) {
        this.inputElement.onscroll = this.syncScrollThrottled;
        // this.inputElement.onscroll = this.syncScroll;
      }
    });
  },
  beforeDestroy() {
    window.removeEventListener('resize', this.calcHeightThrottled);
    this.calcHeightThrottled = null;
    this.syncScrollThrottled = null;
    if (this.inputElement) {
      this.inputElement = this.inputElement.onscroll = null;
    }
  }
};
</script>

<style lang="scss">
$height: 28px;
$lineHeight: 26px;
$padding: 15px;
.ep-message-item {
  &-text {
    position: relative;
    flex-grow: 1;
    // position: absolute;
    // top: 0;
    // left: 0;
    // right: 0;
    // height: $height;
    transition: none;
    overflow: hidden;
  }
  &-backdrop {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    box-sizing: border-box;
    font-size: 13px;
    border: 1px solid transparent;
    z-index: 9;
    font-family: 'Microsoft YaHei', Tahoma, Verdana;
  }
  &-input {
    position: relative;
    display: block;
    z-index: 10;
    font-size: 13px;
    background: transparent;
    height: 100%;
    box-sizing: border-box;
    // height: $height;
    input,
    textarea {
      height: 100%;
      box-sizing: border-box;
      overflow: auto;
      scroll-behavior: auto;
      font-family: 'Microsoft YaHei', Tahoma, Verdana;
      padding: 0 $padding;
      background: transparent;
      line-height: $lineHeight;
      resize: none;
    }
  }
}
/* 幽灵节点 计算高度 */
.ep-message-item-text-ghost,
.ep-message-text-backdrop-item {
  position: absolute;
  padding: 0 $padding;
  box-sizing: border-box;
}
.ep-message-item-text-ghost {
  top: -1000000px;
  left: 0;
  right: 0;
  font-size: 13px;
}
.ep-message-text-backdrop {
  box-sizing: border-box;
  height: 100%;
  overflow: auto;
  transition: none !important;
}
.ep-message-text-backdrop-item {
}
.ep-message-text-backdrop {
  &-item,
  &-kw {
    line-height: 26px;
    vertical-align: top;
  }
}
.ep-message-text-backdrop,
.ep-message-text-backdrop span {
  color: transparent !important;
  height: 100%;
  box-sizing: border-box;
}
</style>
