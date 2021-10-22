<template>
    <div class="ep-entity-list-wrap">
        <div class="ep-entity-list" v-if="list.length" >
            <EntityItem v-for="(item, index) in list" :key="index" :entity="item" :types="typeList"
                @remove-entity="handeleRemove(index, item)"></EntityItem>
        </div>
        <div class="ep-entity-list-empty" v-if="!list.length">
            暂无实体标记
        </div>
    </div>
</template>

<script>
import EntityItem from './EntityItem';
export default {
  name: 'entity-list',
  components: {
    EntityItem
  },
  props: {
    list: {
      type: Array,
      default: () => []
    },
    typeList: {
      type: Array,
      default: () => []
    }
  },
  methods: {
    handeleRemove(index) {
      const idx = index;
      this.list.splice(idx, 1);
    }
  }
};
</script>

<style lang="scss">
.ep-entity-list {
  &-empty {
    padding-top: 4px;
    margin-bottom: 10px;
    position: relative;
    padding-left: 14px;
    line-height: 30px;
    font-size: 13px;
    color: #888;
    &:before {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      display: block;
      border-top: 1px solid #dcdfe6;
      content: '';
    }
  }
}
</style>
