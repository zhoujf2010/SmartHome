<template>
  <div class="ep-message-text-backdrop" ref="backdrop">
    <div class="ep-message-text-backdrop-item" v-for="(entity, index) in entities" :key="index" v-html="genderBackdropHtml(entity)"></div>
  </div>
</template>

<script>
function getScrollBarWidth() {
  let div = document.createElement('div');
  let p = document.createElement('p');

  div.style.display = p.style.display = 'block';
  p.style.height = '100px';
  div.style.padding = 0;
  div.style.border = 'none';
  div.style.overflow = 'auto';
  div.style.height = '10px';

  div.appendChild(p);
  document.body.appendChild(div);

  const w = div.offsetWidth - div.clientWidth;
  div.parentNode.removeChild(div);
  div = p = null;
  return w;
}

const scrollBarWidth = getScrollBarWidth();

export default {
  name: 'text-backdrop',
  props: {
    messageText: {
      type: String,
      default: ''
    },
    entities: {
      type: Array,
      default: () => []
    },
    entityTypes: {
      type: Array,
      default: () => []
    },
    scrollTop: {
      type: Number,
      default: 0
    },
    showScrollBar: {
      type: Boolean,
      default: false
    }
  },
  computed: {
    entityColorMap() {
      const map = {};
      this.entityTypes.forEach(item => {
        map[item.id] = this.hex2rgba(item.bg, 0.3);
      });
      return map;
    },
    rightGap() {
      return this.showScrollBar ? this.scrollBarWidth : 0;
    }
  },
  data() {
    return { scrollBarWidth: scrollBarWidth };
  },
  watch: {
    scrollTop: {
      immediate: true,
      handler(v) {
        this.syncScroll(v);
      }
    },
    entities() {
      this.$nextTick(() => {
        this.syncScroll();
      });
    }
  },
  methods: {
    syncScroll(v) {
      if (this.$refs.backdrop) {
        this.$refs.backdrop.scrollTop = v || this.scrollTop;
      } else {
        setTimeout(() => {
          this.syncScroll();
        }, 20);
      }
    },
    genderBackdropHtml(entity) {
      const selected = this.encodeHtml(this.messageText.substr(entity.start, entity.length));
      const bg = this.entityColorMap[entity.entity] || 'rgba(255,0,0,.3)';
      return this.encodeHtml(this.messageText.substring(0, entity.start)) + `<span class="ep-message-text-backdrop-kw" style="background:${bg}">${selected}</span>` + this.encodeHtml(this.messageText.substr(entity.start + entity.length));
    },
    encodeHtml(value) {
      let div = document.createElement('div');
      div.appendChild(document.createTextNode(value));
      const i = div.innerHTML;
      div = null;
      return i;
    },
    hex2rgba(c, a) {
      a = a || 0.3;
      c = c.substr(1);
      if (c.length === 3) {
        c = c.replace(/([0-9a-fA-f])([0-9a-fA-f])([0-9a-fA-f])/, '$1$1$2$2$3$3');
      }
      var r = parseInt(c.substr(0, 2), 16) || 0,
        g = parseInt(c.substr(2, 2), 16) || 0,
        b = parseInt(c.substr(4, 2), 16) || 0;
      return 'rgba(' + r + ',' + g + ',' + b + ',' + a + ')';
    }
  }
};
</script>
